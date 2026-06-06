import json
import os
import re
import random
from datetime import date
from itertools import groupby
from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from tia_animals.models import Animal, Fact as AnimalFact
from tia_phylo.models import PhyloAnimal, PhyloAnimalLineage, PhyloLineageNode
from tia_taxonomy.models import PhyloDivergence

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)
# _PHYLO_IMG_DIR = Path('/Users/dg/Documents/getphylopics/getphylopics/images')
_PHYLO_IMG_DIR = Path(os.environ.get('PHYLO_IMG_DIR', ''))


PD_LICENSE_TYPES = ['CC0 1.0', 'Public Domain']

GAME_EPOCH = date(2025, 1, 1)


def phylo_image(request, uuid):
    if not _UUID_RE.match(uuid):
        raise Http404
    img_path = _PHYLO_IMG_DIR / f'{uuid}.png'
    if not img_path.exists():
        raise Http404
    return FileResponse(open(img_path, 'rb'), content_type='image/png')


# ── Game helpers ──────────────────────────────────────────────────────────────

def _format_mya_label(mya):
    if mya >= 1:
        return f'~{round(mya):,} million years ago'
    if mya >= 0.001:
        return f'~{round(mya * 1000):,} thousand years ago'
    return f'~{round(mya * 1_000_000):,} years ago'


def _get_game_options(correct_mya, all_myos, rng):
    """Return a shuffled list of 4 MYA values: 1 correct + 3 distractors.

    Tries to include one distractor from a much smaller era, one from a
    much larger era, and one from anywhere, so options aren't trivially easy.
    """
    pool = [m for m in all_myos if m != correct_mya]
    rng.shuffle(pool)

    lower = [m for m in pool if m < correct_mya / 4]
    higher = [m for m in pool if m > correct_mya * 4]
    other = [m for m in pool if m not in lower and m not in higher]

    picks = []
    for bucket in [lower, higher, other]:
        if bucket and len(picks) < 3:
            picks.append(bucket[0])

    # Fill remaining slots if buckets were thin
    used = set(picks)
    for m in pool:
        if len(picks) >= 3:
            break
        if m not in used:
            picks.append(m)
            used.add(m)

    options = [correct_mya] + picks[:3]
    rng.shuffle(options)
    return options

@login_required
def play_hub(request):
    return render(request, 'tia_core/play.html', {'active_tab': 'play'})


@login_required
def game(request):
    today = date.today()
    day_number = (today - GAME_EPOCH).days + 1
    rng = random.Random(today.isoformat())

    # Load all data in bulk — avoids per-pair queries
    all_animals = list(
        PhyloAnimal.objects.order_by('id')
        .values('id', 'uuid', 'common_name', 'taxon_name')
    )
    animal_map = {a['id']: a for a in all_animals}
    animal_ids = list(animal_map)

    extinct_names = set(
        Animal.objects.filter(is_extinct=True).values_list('common_name', flat=True)
    )

    lineage_map = {}
    for row in PhyloAnimalLineage.objects.values('animal_id', 'node_id', 'depth'):
        lineage_map.setdefault(row['animal_id'], {})[row['node_id']] = row['depth']

    node_map = {
        n['id']: n
        for n in PhyloLineageNode.objects.values('id', 'name', 'image_uuid')
    }

    div_map = {d.name: d for d in PhyloDivergence.objects.all()}
    div_by_name = {name: d.divergence_mya for name, d in div_map.items()}
    fact_by_name = {name: d.fun_fact for name, d in div_map.items()}
    all_myos = sorted(set(div_by_name.values()))

    rounds = []
    used_pairs = set()
    attempts = 0

    while len(rounds) < 5 and attempts < 500:
        attempts += 1
        a_id, b_id = rng.sample(animal_ids, 2)
        pair_key = tuple(sorted([a_id, b_id]))
        if pair_key in used_pairs:
            continue
        if a_id not in lineage_map or b_id not in lineage_map:
            continue

        a_map = lineage_map[a_id]
        b_map = lineage_map[b_id]
        shared = set(a_map) & set(b_map)
        if not shared:
            continue

        lca_id = min(shared, key=lambda nid: a_map[nid])
        lca_node = node_map.get(lca_id)
        if not lca_node:
            continue

        correct_mya = div_by_name.get(lca_node['name'])
        if not correct_mya:
            continue

        used_pairs.add(pair_key)
        options_myos = _get_game_options(correct_mya, all_myos, rng)

        d_a = a_map[lca_id]
        d_b = b_map[lca_id]
        path_a = [
            {'name': node_map[nid]['name'], 'image_uuid': node_map[nid]['image_uuid'] or ''}
            for nid, d in sorted(a_map.items(), key=lambda x: x[1])
            if d <= d_a and nid in node_map
        ]
        path_b = [
            {'name': node_map[nid]['name'], 'image_uuid': node_map[nid]['image_uuid'] or ''}
            for nid, d in sorted(b_map.items(), key=lambda x: x[1])
            if d <= d_b and nid in node_map
        ]

        def _animal_data(aid):
            a = animal_map[aid]
            return {k: a[k] for k in ('uuid', 'common_name', 'taxon_name')} | {
                'is_extinct': a['common_name'] in extinct_names
            }

        rounds.append({
            'animal_a': _animal_data(a_id),
            'animal_b': _animal_data(b_id),
            'lca_name': lca_node['name'],
            'lca_image_uuid': lca_node['image_uuid'] or '',
            'lca_fun_fact': fact_by_name.get(lca_node['name'], ''),
            'correct_mya': correct_mya,
            'options': [
                {'mya': mya, 'label': _format_mya_label(mya), 'correct': mya == correct_mya}
                for mya in options_myos
            ],
            'path_a': path_a,
            'path_b': path_b,
        })

    return render(request, 'tia_core/game.html', {
        'rounds_json': json.dumps(rounds),
        'day_number': day_number,
        'today_iso': today.isoformat(),
        'active_tab': 'play',
    })


# ── Explore (renamed from play) ───────────────────────────────────────────────

def _compute_lca(a_id, b_id):
    animal_a = PhyloAnimal.objects.get(id=a_id)
    animal_b = PhyloAnimal.objects.get(id=b_id)

    a_map = {
        row.node_id: row.depth
        for row in PhyloAnimalLineage.objects.filter(animal_id=a_id)
    }
    b_map = {
        row.node_id: row.depth
        for row in PhyloAnimalLineage.objects.filter(animal_id=b_id)
    }

    shared = set(a_map) & set(b_map)
    if not shared:
        return animal_a, animal_b, [], [], None, None

    lca_id = min(shared, key=lambda nid: a_map[nid])
    d_a = a_map[lca_id]
    d_b = b_map[lca_id]

    needed = {nid for nid, d in a_map.items() if d <= d_a}
    needed |= {nid for nid, d in b_map.items() if d <= d_b}
    nodes = {n.id: n for n in PhyloLineageNode.objects.filter(id__in=needed)}

    lca_node = nodes.get(lca_id)
    divergence = PhyloDivergence.objects.filter(name=lca_node.name).first() if lca_node else None

    path_a = [
        {'node': nodes[nid], 'is_lca': nid == lca_id}
        for nid, d in sorted(a_map.items(), key=lambda x: x[1])
        if d <= d_a and nid in nodes
    ]
    path_b = [
        {'node': nodes[nid], 'is_lca': nid == lca_id}
        for nid, d in sorted(b_map.items(), key=lambda x: x[1])
        if d <= d_b and nid in nodes
    ]

    return animal_a, animal_b, path_a, path_b, lca_node, divergence


@login_required
def explore(request):
    all_animals = list(
        PhyloAnimal.objects.order_by('common_name')
        .values('id', 'uuid', 'common_name', 'taxon_name')
    )
    animals_json = json.dumps(list(all_animals))

    if request.method != 'POST':
        return render(request, 'tia_core/explore.html', {
            'animals_json': animals_json,
            'mode': 'picker',
            'active_tab': 'explore',
        })

    try:
        a_id = int(request.POST['animal_a'])
        b_id = int(request.POST['animal_b'])
    except (KeyError, ValueError):
        return render(request, 'tia_core/explore.html', {
            'animals_json': animals_json,
            'mode': 'picker',
            'error': 'Please select two animals.',
            'active_tab': 'explore',
        })

    if a_id == b_id:
        return render(request, 'tia_core/explore.html', {
            'animals_json': animals_json,
            'mode': 'picker',
            'error': 'Please pick two different animals.',
            'active_tab': 'explore',
        })

    animal_a, animal_b, path_a, path_b, lca_node, divergence = _compute_lca(a_id, b_id)

    return render(request, 'tia_core/explore.html', {
        'animals_json': animals_json,
        'animal_a': animal_a,
        'animal_b': animal_b,
        'path_a': path_a,
        'path_b': path_b,
        'lca_node': lca_node,
        'divergence': divergence,
        'mode': 'result',
        'selected_a': a_id,
        'selected_b': b_id,
        'active_tab': 'explore',
    })


# ── Credits ───────────────────────────────────────────────────────────────────

@login_required
def credits(request):
    animals = list(
        PhyloAnimal.objects
        .order_by('common_name')
        .values('uuid', 'common_name', 'taxon_name', 'license_type', 'license_url',
                'contributor_name', 'contributor_url', 'group_name')
    )
    animals_by_letter = [
        (letter, list(grp))
        for letter, grp in groupby(animals, key=lambda a: a['common_name'][0].upper())
    ]
    public_domain_count = sum(1 for a in animals if a['license_type'] in PD_LICENSE_TYPES)
    attribution_count = len(animals) - public_domain_count

    lineage_nodes = list(
        PhyloLineageNode.objects
        .values('name', 'image_uuid', 'license_type', 'license_url', 'contributor_name', 'contributor_url')
    )
    lineage_nodes.sort(key=lambda n: n['name'].lower())
    lineage_by_letter = [
        (letter, list(grp))
        for letter, grp in groupby(lineage_nodes, key=lambda n: n['name'][0].upper())
    ]

    return render(request, 'tia_core/credits.html', {
        'animals_by_letter': animals_by_letter,
        'animal_count': len(animals),
        'animal_letters': sorted(l for l, _ in animals_by_letter),
        'lineage_by_letter': lineage_by_letter,
        'lineage_count': len(lineage_nodes),
        'lineage_letters': sorted(l for l, _ in lineage_by_letter),
        'public_domain_count': public_domain_count,
        'attribution_count': attribution_count,
        'active_tab': 'credits',
    })


# ── Daily Creature ───────────────────────────────────────────────────────────

def _format_creature_status(animal):
    if animal.is_extinct:
        return f"Extinct — {animal.geologic_range}" if animal.geologic_range else "Extinct"
    if animal.conservation_status:
        return f"Living — {animal.conservation_status}"
    return "Living"


def _first_sentence(text):
    if not text:
        return ''
    sentence = text.split('.')[0].strip()
    return (sentence + '.') if sentence else ''


@login_required
def creature_of_day(request):
    today = date.today()
    day_number = (today - GAME_EPOCH).days + 1
    rng = random.Random(f"creature-{today.isoformat()}")

    pa_map = {
        pa['common_name']: pa['uuid']
        for pa in PhyloAnimal.objects.values('common_name', 'uuid')
    }

    all_animals_qs = list(
        Animal.objects
        .select_related('category', 'clade')
        .filter(common_name__in=pa_map)
        .order_by('common_name')
    )

    eligible = list(all_animals_qs)
    rng.shuffle(eligible)
    daily = eligible[0]

    all_parent_groups = sorted({a.category.parent_group for a in all_animals_qs})

    # Pick two distinct facts for clues 3 & 4 (deterministic via seeded rng, names obscured)
    daily_facts = list(AnimalFact.objects.filter(animal=daily).values('text_template'))
    rng.shuffle(daily_facts)
    fact_clues = [
        _obscure_name(f['text_template'], daily.common_name)
        for f in daily_facts[:2]
    ]

    # Sub-group binary: show whenever named sub_groups exist for this parent_group.
    # If the answer IS a named sub_group → one pill glows, others struck.
    # If the answer is "Other" → all named pills struck (meaning "not any of these"),
    # which still filters the grid down without showing the word "Other".
    named_sub_groups = sorted({
        a.category.sub_group
        for a in all_animals_qs
        if a.category.parent_group == daily.category.parent_group
        and a.category.sub_group
        and a.category.sub_group != 'Other'
    })
    answer_sub = daily.category.sub_group or ''
    sub_group_clue = {
        'text': answer_sub if (answer_sub and answer_sub != 'Other') else '',
        'filter_field': 'sub_group',
        'filter_value': answer_sub,
        'type': 'binary',
        'options': [
            {'label': s, 'correct': s == answer_sub}
            for s in named_sub_groups
        ],
    } if named_sub_groups else None

    # Spotlight clues: randomly trim grid to 20 then 10, keeping the answer.
    # Compute baseline pool (mirrors JS getPool after classification clues).
    base_pool = [
        a.common_name for a in all_animals_qs
        if a.category.parent_group == daily.category.parent_group
        and a.is_extinct == daily.is_extinct
        and (not sub_group_clue or a.category.sub_group == answer_sub)
    ]
    non_answer = [n for n in base_pool if n != daily.common_name]
    rng.shuffle(non_answer)

    spotlight_20_clue = None
    spotlight_10_clue = None

    if len(base_pool) > 20:
        keep_20 = [daily.common_name] + non_answer[:19]
        spotlight_20_clue = {
            'text': '20 candidates remain',
            'type': 'spotlight',
            'filter_field': 'spotlight',
            'keep_names': keep_20,
        }
        keep_10 = [daily.common_name] + non_answer[:9]
        spotlight_10_clue = {
            'text': '10 candidates remain',
            'type': 'spotlight',
            'filter_field': 'spotlight',
            'keep_names': keep_10,
        }
    elif len(base_pool) > 10:
        keep_10 = [daily.common_name] + non_answer[:9]
        spotlight_10_clue = {
            'text': '10 candidates remain',
            'type': 'spotlight',
            'filter_field': 'spotlight',
            'keep_names': keep_10,
        }

    clues = [
        c for c in [
            # Clue 1: major group — binary reveal across all groups
            {'text': daily.category.parent_group,
             'filter_field': 'parent_group',
             'filter_value': daily.category.parent_group,
             'type': 'binary',
             'options': [
                 {'label': g, 'correct': g == daily.category.parent_group}
                 for g in all_parent_groups
             ]},
            # Clue 2: living or extinct — binary reveal
            {'text': 'Extinct' if daily.is_extinct else 'Living',
             'filter_field': 'is_extinct',
             'filter_value': daily.is_extinct,
             'type': 'binary',
             'options': [
                 {'label': 'Living',  'correct': not daily.is_extinct},
                 {'label': 'Extinct', 'correct': daily.is_extinct},
             ]},
            # Clue 3: sub-group binary — trims the grid
            sub_group_clue,
            # Clues 4 & 5: fun facts (name obscured)
            {'text': fact_clues[0], 'filter_field': None, 'filter_value': None} if len(fact_clues) > 0 else None,
            {'text': fact_clues[1], 'filter_field': None, 'filter_value': None} if len(fact_clues) > 1 else None,
            # Clues 6 & 7: spotlight — randomly trim to 20 then 10
            spotlight_20_clue,
            spotlight_10_clue,
        ]
        if c is not None
    ]

    all_animals_data = [
        {
            'common_name': a.common_name,
            'scientific_name': a.scientific_name,
            'uuid': pa_map[a.common_name],
            'parent_group': a.category.parent_group,
            'sub_group': a.category.sub_group,
            'is_extinct': a.is_extinct,
        }
        for a in all_animals_qs
    ]

    facts = []
    for f in AnimalFact.objects.filter(animal=daily).values('text_template'):
        try:
            facts.append(f['text_template'].format(animal=daily.common_name))
        except (KeyError, ValueError):
            facts.append(f['text_template'])

    answer = {
        'common_name': daily.common_name,
        'scientific_name': daily.scientific_name,
        'uuid': pa_map[daily.common_name],
        'is_extinct': daily.is_extinct,
        'conservation_status': daily.conservation_status,
        'geologic_range': daily.geologic_range,
        'lifespan_display': daily.lifespan_display,
    }

    return render(request, 'tia_core/creature.html', {
        'clues_json': json.dumps(clues),
        'answer_json': json.dumps(answer),
        'all_animals_json': json.dumps(all_animals_data),
        'facts_json': json.dumps(facts),
        'day_number': day_number,
        'today_iso': today.isoformat(),
        'active_tab': 'play',
    })


# ── Animal Match-Up ───────────────────────────────────────────────────────────

def _obscure_name(text, common_name):
    """Replace the animal's name in fact text so the answer isn't obvious."""
    name_l = common_name.lower()
    # Plural first so "sea otters" doesn't become "this animals"
    text = re.sub(re.escape(name_l + 's'), 'these animals', text, flags=re.IGNORECASE)
    text = re.sub(re.escape(name_l), 'this animal', text, flags=re.IGNORECASE)
    return text


@login_required
def match_up(request):
    today = date.today()
    day_number = (today - GAME_EPOCH).days + 1
    rng = random.Random(f"match-{today.isoformat()}")

    pa_map = {
        pa['common_name']: pa
        for pa in PhyloAnimal.objects.values('common_name', 'taxon_name', 'uuid')
    }
    extinct_names = set(
        Animal.objects.filter(is_extinct=True).values_list('common_name', flat=True)
    )

    # Group facts by animal common_name, only for animals that have phylo data
    facts_by_name = {}
    for row in AnimalFact.objects.select_related('animal').values(
        'text_template', 'animal__common_name'
    ):
        name = row['animal__common_name']
        if name in pa_map:
            facts_by_name.setdefault(name, []).append(row['text_template'])

    eligible = list(facts_by_name.keys())
    rng.shuffle(eligible)
    selected_names = eligible[:20]

    animals_data = []
    for animal_idx, name in enumerate(selected_names):
        pa = pa_map[name]
        fact_text = rng.choice(facts_by_name[name])
        animals_data.append({
            'animal_idx': animal_idx,
            'common_name': name,
            'taxon_name': pa['taxon_name'],
            'uuid': pa['uuid'],
            'fact': _obscure_name(fact_text, name),
        })

    fact_order = list(range(20))
    animal_order = list(range(20))
    rng.shuffle(fact_order)
    rng.shuffle(animal_order)

    rounds = [{
        'facts': [
            {'text': animals_data[i]['fact'], 'animal_idx': animals_data[i]['animal_idx']}
            for i in fact_order
        ],
        'animals': [
            {
                'common_name': animals_data[i]['common_name'],
                'taxon_name': animals_data[i]['taxon_name'],
                'uuid': animals_data[i]['uuid'],
                'animal_idx': animals_data[i]['animal_idx'],
                'is_extinct': animals_data[i]['common_name'] in extinct_names,
            }
            for i in animal_order
        ],
    }]

    return render(request, 'tia_core/match.html', {
        'rounds_json': json.dumps(rounds),
        'day_number': day_number,
        'today_iso': today.isoformat(),
        'active_tab': 'play',
    })
