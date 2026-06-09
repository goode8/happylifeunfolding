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


BEFORE_MAMMALS_ROUNDS = [
    {
        "name": "Dimetrodon",
        "uuid": "ee7f1c8c-c98d-4611-aa4e-c112e86782e6",
        "group": "Pelycosaur · Early Synapsid",
        "period": "~295 million years ago",
        "emoji": "🦎",
        "innovation": "Differentiated teeth",
        "teach_text": "Dimetrodon looks like a dinosaur but it's actually more closely related to you than to any dinosaur or modern lizard. Its big leap: different types of teeth — incisors to grab, canines to tear, and cheek teeth to grind. Every creature before this had rows of identical cone-shaped teeth, like a shark.",
        "fun_fact": "That iconic sail on its back was probably for thermoregulation — warming up in the sun or cooling off in the breeze. An early hint that this lineage cared a lot about body temperature.",
        "size": "About 3 meters long — closer to a large crocodile than a T. rex",
        "locomotion": "Four legs with a sprawling, lizard-like gait — belly close to the ground",
        "diet": "Carnivore — fish, large amphibians, and other animals",
        "habitat": "Swampy river floodplains and coastal lowlands",
        "climate": "Hot and humid — equatorial tropics with strong wet and dry seasons",
        "landmass": "Pangaea — what is now Texas, Oklahoma, and parts of Germany",
        "quiz_question": "What advantage did having different tooth types give Dimetrodon over animals with identical teeth?",
        "options": [
            {"text": "Its teeth were harder and less likely to break", "correct": False, "explanation": "Tooth hardness is about enamel, not shape — identical teeth can be just as hard."},
            {"text": "It could grow replacement teeth throughout its life", "correct": False, "explanation": "Actually the opposite — many reptiles with identical teeth can replace them continuously. Specialized teeth tend to be replaced less freely."},
            {"text": "It could eat a much wider variety of food", "correct": True, "explanation": "Different teeth handle different textures — gripping, tearing, grinding. This opened up a far wider menu than rows of identical spike-teeth ever could."},
            {"text": "It could sense which food was safe to eat", "correct": False, "explanation": "Teeth don't detect food safety — that's the job of smell and taste."},
        ],
    },
    {
        "name": "Inostrancevia",
        "uuid": "730f5066-4b02-4548-be22-6d683af13d70",
        "group": "Gorgonopsian · Therapsid",
        "period": "~260 million years ago",
        "emoji": "🐅",
        "innovation": "Saber-like canine teeth",
        "teach_text": "Inostrancevia was a top predator the size of a bear, with enormous saber-like canine teeth and a jaw that could open nearly 90 degrees. This was a new predator strategy: ambush and stab rather than grab-and-shake. Gorgonopsians ruled as apex predators for millions of years before the Permian extinction wiped them out entirely.",
        "fun_fact": "Despite the ferocious teeth, Inostrancevia's limbs were already held more upright under its body — more like a dog than a crocodile's sprawl. Another quiet step toward the mammal body plan.",
        "size": "About 3.5 meters long — the size of a large bear",
        "locomotion": "Four legs held more upright than a lizard, but still somewhat sprawling",
        "diet": "Carnivore — hunted large plant-eaters like Lystrosaurus",
        "habitat": "Open semi-arid plains and scrublands",
        "climate": "Hot and increasingly dry — the late Permian was trending toward arid conditions across Pangaea's interior",
        "landmass": "Pangaea — what is now the Perm region of northern Russia",
        "quiz_question": "Much later, a completely unrelated mammal independently evolved the same enormous saber-tooth strategy. Which one?",
        "options": [
            {"text": "Smilodon", "correct": True, "explanation": "Smilodon independently solved the same problem 250 million years later. Same challenge, same answer — this is called convergent evolution."},
            {"text": "Dire Wolf", "correct": False, "explanation": "Dire wolves had large teeth but not elongated saber-like canines — they hunted very differently."},
            {"text": "Megalodon", "correct": False, "explanation": "Megalodon used rows of serrated teeth for slicing, not enlarged canines for stabbing."},
            {"text": "Velociraptor", "correct": False, "explanation": "Velociraptors were dinosaurs — a completely different lineage — and relied more on claws than teeth."},
        ],
    },
    {
        "name": "Lystrosaurus",
        "uuid": "b4b49b73-e13a-4f5b-8fda-2bf6d6dcb1eb",
        "group": "Dicynodont · Therapsid",
        "period": "~255 million years ago",
        "emoji": "🦏",
        "innovation": "Beak replacing most teeth",
        "teach_text": "Lystrosaurus replaced almost all its teeth with a tough, horny beak — like a turtle — keeping only two small tusks. Losing teeth sounds like a disadvantage, but Lystrosaurus survived the Permian-Triassic extinction (~252 million years ago), the worst in Earth's history, when over 90% of all species died. After the catastrophe, Lystrosaurus briefly made up the vast majority of all land animals on Earth.",
        "fun_fact": "Some estimates suggest Lystrosaurus made up over 90% of land vertebrates in the Early Triassic. The world after the extinction was almost entirely Lystrosaurus.",
        "size": "About 1 meter long — stocky and low-slung, roughly pig-sized",
        "locomotion": "Four short legs with a semi-sprawling gait, built for digging and rooting",
        "diet": "Herbivore — used its beak to clip plants and dig up roots and tubers",
        "habitat": "River floodplains and semi-arid basins — highly adaptable",
        "climate": "Extreme heat and high CO2 in the aftermath of the Permian-Triassic extinction (~252 million years ago) — one of the harshest climates in Earth's history",
        "landmass": "Pangaea — fossils found in South Africa, Antarctica, India, Russia, and China. Its global spread helped scientists prove continental drift.",
        "quiz_question": "Why did having a beak likely help Lystrosaurus survive when most life on Earth died?",
        "options": [
            {"text": "Its beak was armor against predators", "correct": False, "explanation": "A beak on the face wouldn't protect the body from predators."},
            {"text": "Beaks grow back if damaged", "correct": False, "explanation": "Beaks can regrow somewhat, but that's not why Lystrosaurus survived."},
            {"text": "It breathed through its beak like a snorkel", "correct": False, "explanation": "No evidence for this — it breathed normally through its nostrils."},
            {"text": "It could eat tough roots, bark, and dry plants that others couldn't", "correct": True, "explanation": "After the extinction, lush plant life collapsed. Animals that could eat tough or buried vegetation had a huge survival advantage."},
        ],
    },
    {
        "name": "Thrinaxodon",
        "uuid": "94fda119-5435-4246-ad23-20b15f3bcb8d",
        "group": "Cynodont · Early Cynodontia",
        "period": "~250 million years ago",
        "emoji": "🦦",
        "innovation": "Whisker pits (evidence of fur)",
        "teach_text": "Thrinaxodon was weasel-sized, and its skull shows small pits where whisker nerve roots attach — almost certain proof it had whiskers, which means fur. Fur only makes sense if an animal generates its own body heat; a cold-blooded animal has no use for insulation. Thrinaxodon is our earliest ancestor with strong fossil evidence for being warm-blooded.",
        "fun_fact": "Thrinaxodon burrows have been found containing multiple animals sheltering together — suggesting it may have cared for young in a sheltered nest, another behavior on the road to mammals.",
        "size": "About 30–50 cm long — similar to a ferret or large weasel",
        "locomotion": "Four legs with a more upright stance than earlier synapsids — agile and quick",
        "diet": "Carnivore and insectivore — small animals, insects, and eggs",
        "habitat": "Burrows dug into riverbanks and floodplains — a sheltered, tunneling lifestyle",
        "climate": "Early Triassic recovery — still very hot and harsh, slowly stabilizing after the mass extinction",
        "landmass": "Pangaea — what is now South Africa and Antarctica, which were then adjacent",
        "quiz_question": "Why do whisker pits in a fossil tell paleontologists the animal was likely warm-blooded?",
        "options": [
            {"text": "Only warm-blooded animals have nerves in their face", "correct": False, "explanation": "All vertebrates have facial nerves — cold-blooded animals have them too."},
            {"text": "Fur only helps animals that generate their own body heat — cold-blooded animals don't need insulation", "correct": True, "explanation": "Insulation traps your own warmth. If you rely on the sun to warm up, a fur coat actually gets in the way."},
            {"text": "Reptiles have whisker pits too, just hidden under scales", "correct": False, "explanation": "No reptile has whisker pits — this feature is exclusive to the mammal lineage."},
            {"text": "Whiskers help animals directly detect body temperature", "correct": False, "explanation": "Whiskers detect nearby objects and air movement, not temperature."},
        ],
    },
    {
        "name": "Cynognathus",
        "uuid": "6cbe14b2-022a-4982-82c0-53c0e0fb5cb8",
        "group": "Cynodont · Advanced Cynodontia",
        "period": "~245 million years ago",
        "emoji": "🐺",
        "innovation": "Secondary palate",
        "teach_text": "Cynognathus was wolf-sized and had a fully formed secondary palate — a bony shelf across the roof of its mouth separating the nasal passage from the oral cavity. You have this too: feel the hard front part of the roof of your mouth. Without it, every chew interrupts breathing. With it, an animal can eat for long stretches, which is essential when you're warm-blooded and need constant fuel.",
        "fun_fact": "Cynognathus also had a lower jaw that was nearly one single bone — compared to the many small bones in fish and reptile jaws. It was zeroing in on the modern mammalian jaw design.",
        "size": "About 1.2 meters long — the build of a large dog or small wolf",
        "locomotion": "Four legs with a more erect, dog-like stance — one of the first animals to walk this way",
        "diet": "Carnivore — an active pursuit predator that hunted large animals",
        "habitat": "Open floodplains and dry river valleys",
        "climate": "Early Triassic — warm and dry, with Pangaea's vast interior becoming increasingly arid",
        "landmass": "Pangaea — fossils found in South Africa, Argentina, and Antarctica. Like Lystrosaurus, its range helped confirm continental drift.",
        "quiz_question": "Mammal babies nurse for weeks or months. How does the secondary palate make prolonged nursing possible?",
        "options": [
            {"text": "It makes the mouth larger to hold more milk", "correct": False, "explanation": "The palate separates nasal and oral passages — it doesn't change mouth size."},
            {"text": "It keeps milk warm inside the mouth", "correct": False, "explanation": "The palate is bone — it doesn't insulate or heat anything."},
            {"text": "Babies can breathe through their nose while their mouth is sealed around a nipple", "correct": True, "explanation": "Without the secondary palate, a nursing baby would have to choose between swallowing and breathing. The palate lets both happen at once."},
            {"text": "It helps babies taste the milk better", "correct": False, "explanation": "Taste buds are on the tongue — the palate plays no role in taste."},
        ],
    },
    {
        "name": "Morganucodon",
        "uuid": "be4fd4ac-7dfb-4dbc-bdb8-6be298aa9015",
        "group": "Early Mammaliaform",
        "period": "~210 million years ago",
        "emoji": "🐭",
        "innovation": "Three middle ear bones",
        "teach_text": "Morganucodon was shrew-sized — one of the first true mammals. Its defining feature: three tiny bones in the middle ear (hammer, anvil, and stirrup) that amplified high-frequency sounds. These bones came directly from jaw bones used by earlier synapsids. You have these exact three bones right now, in each of your ears. The repurposing of old jaw bones into your hearing is one of the most remarkable transformations in all of vertebrate evolution.",
        "fun_fact": "Morganucodon were likely awake mostly at night, hunting insects while dinosaurs slept. That nocturnal lifestyle may have actually driven the development of sharper hearing — you need good ears when you can't rely on your eyes.",
        "size": "About 9 cm long and 20–30 grams — similar to a large mouse",
        "locomotion": "Four legs, small and nimble, likely able to climb — not unlike a modern shrew",
        "diet": "Insectivore — hunted insects and small invertebrates at night",
        "habitat": "Forest floors, leaf litter, and rock crevices — probably burrowed as well",
        "climate": "Late Triassic — warm and mostly dry; Pangaea just beginning to slowly rift apart",
        "landmass": "Pangaea in its later stages — fossils found in Wales (UK) and Yunnan Province, China",
        "quiz_question": "The three middle ear bones were jaw bones in our earlier ancestors. What does this tell us about how evolution works?",
        "options": [
            {"text": "Evolution repurposes existing structures for new jobs rather than building from scratch", "correct": True, "explanation": "This is one of the clearest examples in all of evolution. The same bones that closed a jaw now amplify sound. Evolution tinkers — it doesn't design fresh."},
            {"text": "Evolution always makes structures more complex over time", "correct": False, "explanation": "Evolution doesn't have a direction — it can simplify or complicate structures depending on what helps survival."},
            {"text": "Mammals evolved from animals that were completely deaf", "correct": False, "explanation": "Earlier synapsids could hear — they just used different configurations of the same bones."},
            {"text": "Jaw bones are always the weakest part of the skeleton", "correct": False, "explanation": "This has nothing to do with strength — it's about bones being repurposed for a new function."},
        ],
    },
]


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


@login_required
def before_mammals(request):
    return render(request, 'tia_core/before_mammals.html', {
        'rounds_json': json.dumps(BEFORE_MAMMALS_ROUNDS),
        'active_tab': 'play',
    })


PANGAEA_TO_NOW_ROUNDS = [
    {
        "name": "Pangaea",
        "group": "Supercontinent · Late Carboniferous",
        "period": "~335–175 million years ago",
        "emoji": "🌍",
        "innovation": "All land fused into one",
        "slides": [
            {
                "label": "The Big Picture",
                "title": "When Earth had just one landmass",
                "body": "Around 335 million years ago, the slow grind of tectonic plates brought all of Earth's land together into a single supercontinent: Pangaea. It stretched from pole to pole, covering roughly a third of the planet's surface. On its eastern side, a warm tropical bay called the Tethys Sea cut inland — an ancestor of today's Mediterranean. The rest of the ocean — a single enormous body of water called Panthalassa — covered everything else. For 160 million years, every piece of land you know was connected.",
                "details": [
                    {"key": "Span", "value": "~160 million years (335–175 Ma); earlier supercontinents assembled and split before this one"},
                    {"key": "Today", "value": "Fully broken apart — its pieces are today's seven continents"},
                ],
            },
            {
                "label": "Life & Climate",
                "title": "Hot, arid, and ruled by proto-mammals",
                "body": "Pangaea's interior received almost no rainfall — too far from any coast for moisture to reach. A vast arid interior dominated the centre of the landmass. The coasts were hit by a giant monsoon that swung seasonally across the entire continent. Early synapsids — the lineage leading to mammals — were the dominant large animals. Dimetrodon ruled as apex predator 300 million years ago; Lystrosaurus survived the worst extinction in Earth's history near Pangaea's end. The first dinosaurs only appeared around 230 million years ago, near the very end.",
                "details": [
                    {"key": "Climate", "value": "Hot, arid interior with a vast mega-monsoon cycle; coasts wetter; no permanent polar ice caps"},
                    {"key": "Life", "value": "Early synapsids (Dimetrodon, Lystrosaurus), first archosaurs; dinosaurs arrived only near the very end"},
                ],
            },
            {
                "label": "The Breakup",
                "title": "A rift, a flood basalt, a new ocean",
                "body": "Pangaea didn't split quietly. Around 201 million years ago, a massive series of volcanic eruptions — the Central Atlantic Magmatic Province (CAMP) — flooded eastern North America and northwest Africa with enormous lava fields and pumped enough CO₂ into the atmosphere to trigger a mass extinction at the Triassic-Jurassic boundary. As the rift widened over millions of years, seawater flooded in. The proto-Atlantic started as a narrow seaway no wider than the modern Red Sea. It has been growing at about 2.5 cm per year ever since and is still widening today.",
                "details": [
                    {"key": "Feature", "value": "The Tethys Sea — a tropical ocean on Pangaea's eastern side; ancestor of today's Mediterranean"},
                    {"key": "Evidence", "value": "Matching rock layers, glacial deposits, and identical land animal fossils (Lystrosaurus) found on now-separate continents"},
                ],
                "fun_fact": "Alfred Wegener proposed Pangaea in 1912 and was ridiculed for decades. The proof came in the 1960s when seafloor mapping revealed that new ocean crust was forming at mid-ocean ridges — the ocean floor itself was spreading, pushing the continents apart. The evidence supported his model in full.",
            },
        ],
        "quiz_question": "What's the most compelling evidence that Pangaea actually existed?",
        "options": [
            {"text": "Ancient maps show all the continents connected", "correct": False, "explanation": "No maps from 300 million years ago exist — humans weren't around. The evidence comes from rock layers and fossils."},
            {"text": "Identical fossils of the same land animals appear on continents now separated by thousands of miles of ocean", "correct": True, "explanation": "The land reptile Lystrosaurus appears in South Africa, India, Antarctica, and China. There's no way those animals swam the Atlantic — the land had to be connected."},
            {"text": "The continents look like puzzle pieces that fit together", "correct": False, "explanation": "Visual fit is suggestive but not proof. The real evidence is matching rock strata, glacial deposits, and identical fossils on opposite sides of oceans."},
            {"text": "Deep-sea drilling found Pangaea-era rocks at the bottom of the Atlantic", "correct": False, "explanation": "The Atlantic seafloor is actually young — the oldest Atlantic crust is only ~180 million years old. The ocean itself formed as Pangaea split."},
        ],
    },
    {
        "name": "Gondwana",
        "group": "Southern Supercontinent · Jurassic",
        "period": "~175 million years ago",
        "emoji": "🗺️",
        "innovation": "Pangaea splits; southern continents drift apart",
        "slides": [
            {
                "label": "The Big Picture",
                "title": "Pangaea's southern half",
                "body": "When Pangaea broke apart, it divided into two major landmasses: Laurasia in the north (today's North America, Europe, and Asia) and Gondwana in the south (today's South America, Africa, Antarctica, Australia, and India). The Tethys Sea expanded between them into a full ocean. But while Laurasia began fragmenting relatively quickly, Gondwana stayed largely intact for tens of millions of years longer — its pieces separating gradually, one by one, over more than 100 million years.",
                "details": [
                    {"key": "Span", "value": "Gondwana first assembled ~550 Ma; fully broke apart ~130–30 Ma depending on which fragment"},
                    {"key": "Today", "value": "South America, Africa, Antarctica, Australia, India, and parts of southern Europe and the Middle East"},
                ],
            },
            {
                "label": "India's Journey",
                "title": "The fastest-moving continent",
                "body": "Of all the Gondwana fragments, India traveled the farthest and fastest. When it detached from Africa and Antarctica around 130 million years ago, it became an island continent drifting northward across the Tethys Sea at up to 20 cm per year — faster than any tectonic plate before or since. The Tethys seafloor dove beneath Asia as India approached. Then, roughly 50–40 million years ago, India finally docked into Asia. With the ocean floor gone, the two continental crusts had nowhere to go but up. The result was the Himalayas — the tallest mountains on Earth, still rising today at about 5 mm per year.",
                "details": [
                    {"key": "Climate", "value": "Warm and humid on Gondwana's coasts; drier interior; India's northward journey crossed equatorial climates"},
                    {"key": "Life", "value": "Long-necked sauropod dinosaurs spread across Gondwana; isolation after fragmentation shaped distinct fauna on each piece"},
                ],
            },
            {
                "label": "The Last Fragment",
                "title": "How Antarctica froze solid",
                "body": "Australia and Antarctica were the last Gondwana fragments to separate, around 35–30 million years ago. When they finally pulled apart, a gap opened to the south — and for the first time, a continuous current began circling Antarctica: the Antarctic Circumpolar Current. This current — the most powerful ocean current on Earth today — acts as a thermal barrier, isolating Antarctic waters from warmer ocean basins. Within a few million years, Antarctica went from a continent warm enough to host forests to a permanent ice sheet. That ice sheet now holds about 70% of Earth's fresh water.",
                "details": [
                    {"key": "Feature", "value": "The proto-South Atlantic — a new ocean opening as Africa and South America pulled apart from ~130 Ma"},
                    {"key": "Evidence", "value": "The Glossopteris fern fossil appears across all Gondwana fragments; matching glacial deposits and rock strata on separate continents"},
                ],
                "fun_fact": "Scientists have found fossil wood, leaves, and even fossil rainforest pollen in Antarctica. As recently as 34 million years ago, it was warm enough there to support forests. When the Southern Ocean formed, a forested continent became a frozen one within a few million years.",
            },
        ],
        "quiz_question": "India was once part of Gondwana in the southern hemisphere. What happened when it finally crashed into Asia?",
        "options": [
            {"text": "The collision caused mass extinctions across Asia", "correct": False, "explanation": "The India-Asia collision was gradual over millions of years — too slow to cause mass extinctions."},
            {"text": "It built the Himalayas — the tallest mountains on Earth today", "correct": True, "explanation": "India began colliding with Asia roughly 50–40 million years ago. The ongoing collision still pushes the Himalayas higher by about 5 mm per year."},
            {"text": "It created a deep ocean trench between India and Asia", "correct": False, "explanation": "A trench forms when one plate dives under another. Instead, both continental plates buckled upward, producing mountains."},
            {"text": "India slid under Asia and disappeared into the mantle", "correct": False, "explanation": "Continental crust is too buoyant to subduct — it crumples and stacks up instead, which is how mountain ranges form."},
        ],
    },
    {
        "name": "Morrison Formation",
        "group": "Late Jurassic · Western North America",
        "period": "~155–148 million years ago",
        "emoji": "🦕",
        "innovation": "Vast river floodplain — the richest dinosaur site on Earth",
        "slides": [
            {
                "label": "The Place",
                "title": "A vast semi-arid floodplain",
                "body": "155 million years ago, the area now covered by Wyoming, Utah, Colorado, Montana, and neighboring states was a broad flat floodplain crossed by rivers draining eastward from the newly rising mountains to the west. The climate was strongly seasonal: long dry seasons followed by heavy monsoon rains that swelled rivers across the plain. When animals died near rivers and lakes, they were buried in sediment. Layer by layer, those sediments hardened into rock. That rock layer — the Morrison Formation — is now one of the most fossil-rich geological units on Earth.",
                "details": [
                    {"key": "Span", "value": "Deposited over ~8 million years (155–148 Ma); now exposed at the surface across the American West"},
                    {"key": "Today", "value": "Wyoming, Utah, Colorado, Montana, South Dakota, New Mexico — visit Dinosaur National Monument in Utah"},
                ],
            },
            {
                "label": "The Giants",
                "title": "Sauropod giants",
                "body": "The Morrison floodplain was home to some of the largest land animals ever known. Brachiosaurus weighed up to 56 tonnes — as much as eight African elephants — and stood 13 meters tall at the shoulder. Diplodocus stretched 26 meters long. These sauropods browsed the high canopy of trees, their long necks working like a giraffe's but on a vastly larger scale. Allosaurus was the apex predator: a 10-meter, 2-tonne carnivore that hunted in a landscape crowded with prey. Stegosaurus used its distinctive back plates for heat regulation and species display. The Morrison has yielded over 75 named dinosaur species — more than any other single rock formation on Earth.",
                "details": [
                    {"key": "Climate", "value": "Seasonal — long dry period followed by monsoon rains; warm and subtropical overall; no ice caps anywhere"},
                    {"key": "Life", "value": "Allosaurus, Stegosaurus, Brachiosaurus, Diplodocus, Apatosaurus, Camarasaurus, and 70+ other species"},
                ],
            },
            {
                "label": "Discovery",
                "title": "The Bone Wars",
                "body": "The first major Morrison fossils were found in 1877 near Morrison, Colorado and Como Bluff, Wyoming. The discovery ignited a bitter two-decade rivalry between paleontologists Othniel Charles Marsh at Yale and Edward Drinker Cope in Philadelphia. They hired spies, bribed each other's workers, and sometimes deliberately smashed fossils to prevent the other from using them. Between them they named over 130 new dinosaur species — many duplicates, creating a taxonomic mess that took decades to untangle. But their frantic competition produced the first scientific picture of the Jurassic world, including names still used today.",
                "details": [
                    {"key": "Feature", "value": "Bone beds — dense fossil accumulations where hundreds of animals died near shrinking water holes during dry seasons"},
                    {"key": "Evidence", "value": "Thousands of quarry sites; rock layers alternate between river channel, floodplain soil, and pond deposits in seasonal cycles"},
                ],
                "fun_fact": "Dinosaur National Monument in Utah sits directly on a Morrison bone bed. In 1909, paleontologist Earl Douglass found 10 Apatosaurus vertebrae weathering out of a hillside. The excavation that followed yielded over 1,500 bones — and a building was eventually constructed around the cliff face to preserve it.",
            },
        ],
        "quiz_question": "Why did so many Morrison Formation dinosaurs die near the same spots, creating the dense bone beds we find today?",
        "options": [
            {"text": "Volcanic eruptions buried entire herds at once", "correct": False, "explanation": "Volcanic ash can preserve fossils, but Morrison bone beds are found in river and floodplain deposits, not volcanic layers."},
            {"text": "Predators herded prey animals into natural traps", "correct": False, "explanation": "Some predator-prey accumulations exist, but the largest bone beds contain many species mixed together — not hunting events."},
            {"text": "During seasonal droughts, animals crowded around shrinking water holes and died in large numbers", "correct": True, "explanation": "As rivers dried up each dry season, hundreds of animals from many species concentrated at the last remaining water. Mass die-offs deposited bones together in layers now exposed as fossil sites."},
            {"text": "A single giant flood swept them all into one river delta", "correct": False, "explanation": "Flood-deposited sites exist, but the characteristic Morrison deposits show repeated drought-driven death events across many seasons — not one catastrophic flood."},
        ],
    },
    {
        "name": "Western Interior Seaway",
        "group": "Late Cretaceous · North America",
        "period": "~85 million years ago",
        "emoji": "🌊",
        "innovation": "Inland sea split North America from Gulf to Arctic",
        "slides": [
            {
                "label": "The Geography",
                "title": "North America, cut in two",
                "body": "From roughly 100 to 66 million years ago, a shallow inland sea split the North American continent completely in half — from the Gulf of Mexico all the way to the Arctic Ocean. The Western Interior Seaway was about 3,000 km long and up to 970 km wide. Denver sat under tens of meters of warm water. Kansas was seafloor. The seaway formed as global temperatures rose (driven by intense volcanic activity) and sea levels followed, flooding the low-lying basin east of the rising Rocky Mountains. It was never deep — mostly 100–200 meters — but it was warm, salty, and teeming with life.",
                "details": [
                    {"key": "Span", "value": "~34 million years (100–66 Ma); drained as the Rockies rose and sea levels fell at the K-Pg boundary"},
                    {"key": "Today", "value": "The Great Plains — the chalky seafloor is now the Niobrara Formation, visible as white cliffs in western Kansas"},
                ],
            },
            {
                "label": "Sea Monsters",
                "title": "Mosasaurs, plesiosaurs, and 6-meter fish",
                "body": "Mosasaurs — giant marine lizards related to modern monitor lizards — ruled as apex predators. Tylosaurus reached 14 meters; Mosasaurus was even larger. Long-necked plesiosaurs like Styxosaurus had necks longer than their bodies, with over 70 neck vertebrae. Xiphactinus was a 6-meter predatory fish with a massive gaping jaw that could swallow prey nearly its own size whole. The seafloor was carpeted in chalk — billions of microscopic algae (coccoliths) that rained down for millions of years, eventually forming the Niobrara chalk still visible as white cliffs in western Kansas today.",
                "details": [
                    {"key": "Climate", "value": "Warm subtropical; global temperatures 4–10°C higher than today; sea surface ~35°C in tropics; no polar ice caps"},
                    {"key": "Life", "value": "Sea: mosasaurs, plesiosaurs, ammonites, giant turtles; western shore: T. rex, Triceratops, Ankylosaurus, hadrosaurs"},
                ],
            },
            {
                "label": "The Shores & Aftermath",
                "title": "T. rex lived on the beach",
                "body": "The land flanking the seaway's western shore was crowded with dinosaurs that now fill natural history museums — T. rex, Triceratops, Ankylosaurus, and hadrosaurs like Edmontosaurus all lived in what is now Montana and Wyoming. Their fossils come from the Hell Creek Formation: rocks that represent those western shoreline environments at the very end of the Cretaceous. When the asteroid hit 66 million years ago, the seaway was already retreating as the Rockies rose. The asteroid's aftermath accelerated the process; the seaway drained over millions of years, leaving behind the flat sedimentary deposits that are now the Great Plains.",
                "details": [
                    {"key": "Feature", "value": "The Niobrara chalk — thick white rock formed from microscopic algae (coccoliths) raining down for millions of years"},
                    {"key": "Evidence", "value": "Marine fossils (mosasaur bones, ammonites, shark teeth) found hundreds of km inland; the white chalk cliffs of Kansas"},
                ],
                "fun_fact": "In 1872, paleontologist Edward Cope described a plesiosaur so long-necked that he initially mounted the skull on the tail end. His rival Othniel Marsh pointed out the error publicly — deepening the Bone Wars rivalry that occupied both men for the rest of their careers.",
            },
        ],
        "quiz_question": "When the Western Interior Seaway drained at the end of the Cretaceous, what did it leave behind?",
        "options": [
            {"text": "The Rocky Mountains", "correct": False, "explanation": "The Rockies were forming on the western edge at the same time — it was actually the rising Rockies that helped drain the seaway by lifting the surrounding land."},
            {"text": "The Great Lakes", "correct": False, "explanation": "The Great Lakes were carved by glaciers during the last Ice Age, about 20,000 years ago — vastly more recently."},
            {"text": "The flat sedimentary layers that became the Great Plains", "correct": True, "explanation": "As the seaway retreated, it left a thick, flat layer of marine sediments. Those sediments, now elevated above sea level, became the Great Plains of Kansas, Nebraska, and the Dakotas."},
            {"text": "The Mississippi River", "correct": False, "explanation": "The Mississippi flows through the former seaway zone, but the river itself developed long after, shaped mainly by glacial meltwater during the Ice Ages."},
        ],
    },
    {
        "name": "Chicxulub Impact",
        "group": "K-Pg Boundary · Yucatan",
        "period": "~66 million years ago",
        "emoji": "☄️",
        "innovation": "Asteroid impact ended the age of non-bird dinosaurs",
        "slides": [
            {
                "label": "The Impact",
                "title": "66 million years ago, in under a minute",
                "body": "A rock roughly 10–15 km wide entered Earth's atmosphere traveling at 20 km per second. In moments it struck the shallow sea covering what is now the Yucatan Peninsula. The explosion released roughly as much energy as the Sun delivers to Earth over an entire month — concentrated into a few seconds. It vaporized the asteroid, the surrounding seafloor, and thousands of cubic kilometers of rock instantly. A fireball expanded at hypersonic speed. Within minutes, tsunamis radiated across the Gulf of Mexico, their waves hundreds of meters high. The seismic shock reached every part of the planet simultaneously. Rock debris lofted into the upper atmosphere came back down as a global rain of hot material, radiating enough heat to ignite fires across wide regions.",
                "details": [
                    {"key": "Span", "value": "Impact lasted seconds; 'impact winter' lasted years to decades; full ecosystem recovery took millions of years"},
                    {"key": "Today", "value": "Crater center beneath Chicxulub Puerto, Yucatan, Mexico; extends into Gulf of Mexico; ~180 km wide"},
                ],
            },
            {
                "label": "The Aftermath",
                "title": "The day the sky went dark",
                "body": "In the months and years that followed, sulfur from the vaporized seafloor and soot from fires blocked sunlight, halting photosynthesis for months to years. Temperatures dropped sharply. Plants died globally. 75% of all species went extinct — including every non-bird dinosaur, all pterosaurs, all marine reptiles, and the ammonites. Forests were leveled globally; conifers and flowering trees died back on a massive scale, and full forest recovery took thousands to millions of years depending on the region. Ferns, which spread by airborne spores, colonized the bare landscape first — their spores so dominate the rock record right at the impact layer that geologists call it the fern spike. Animals that survived tended to be small, cold-tolerant, and able to eat almost anything: insects (most orders made it through), early mammals, birds, crocodilians, turtles, lizards, and frogs.",
                "details": [
                    {"key": "Climate", "value": "Impact winter: near-total darkness, global wildfires, temperature collapse; then centuries of CO₂-driven warming after dust settled"},
                    {"key": "Life", "value": "Wiped out: non-bird dinosaurs, pterosaurs, mosasaurs, ammonites, most forest trees and flowering plants. Survived: ferns (first colonizers), most insects, small mammals, birds, crocodilians, turtles, frogs"},
                ],
            },
            {
                "label": "The Discovery",
                "title": "Iridium, cenotes, and a Mexican oil survey",
                "body": "In 1980, physicist Luis Alvarez and his geologist son Walter discovered something strange: at exactly the K-Pg boundary in rocks worldwide, there was a thin layer of iridium — a metal almost vanishingly rare on Earth but common in asteroids. They proposed an impact. Most scientists were skeptical. The crater wasn't identified until 1991, when researchers realized that gravity anomaly maps of the Yucatan — originally collected by the Mexican oil company Pemex in 1978 and mostly ignored — showed a buried ring structure 180 km wide. The crater's surface expression is still visible: a semicircular ring of freshwater sinkholes called cenotes, sacred wells of the ancient Maya.",
                "details": [
                    {"key": "Feature", "value": "The global iridium layer — a thin worldwide band of iridium in rock from exactly 66 Ma, found on every continent"},
                    {"key": "Evidence", "value": "Buried Chicxulub crater; global iridium anomaly; shocked quartz; glass spherules ejected worldwide"},
                ],
                "fun_fact": "The Deccan Traps in India — enormous volcanic eruptions happening around the same time — were also stressing the global ecosystem. Scientists still debate how much the Deccan volcanism contributed versus the asteroid alone. The current consensus: the asteroid was the primary cause, but the volcanoes didn't help.",
            },
        ],
        "quiz_question": "How did scientists first determine the K-Pg extinction was caused by an asteroid rather than volcanism?",
        "options": [
            {"text": "They found the Chicxulub crater first, then connected it to the extinction", "correct": False, "explanation": "Actually the reverse: the iridium layer and extinction link were established first (1980). Chicxulub wasn't confirmed as the impact site until the early 1990s."},
            {"text": "A worldwide layer of iridium — rare on Earth but common in asteroids — appears in rock from exactly 66 Ma on every continent", "correct": True, "explanation": "The Alvarez team discovered in 1980 that a thin iridium-rich layer appears globally at the K-Pg boundary. The only known mechanism for simultaneous worldwide iridium deposition is an asteroid impact."},
            {"text": "Fossils show animals slowly dying off over thousands of years, proving a gradual volcanic cause", "correct": False, "explanation": "The opposite: the fossil record shows an abrupt cutoff — millions of species disappearing at the same geological moment. Sudden cutoffs indicate catastrophe; gradual die-offs indicate volcanism."},
            {"text": "Drill cores from the crater contained identifiable asteroid fragments", "correct": False, "explanation": "Scientific drilling at Chicxulub confirmed the impact structure, but the primary evidence for the impact-extinction link was the worldwide iridium layer, not crater fragments."},
        ],
    },
    {
        "name": "Isthmus of Panama",
        "group": "Pliocene · Central America",
        "period": "~3–4 million years ago",
        "emoji": "🌎",
        "innovation": "Land bridge connected the Americas; split Atlantic from Pacific",
        "slides": [
            {
                "label": "The Formation",
                "title": "Two oceans, then one land bridge",
                "body": "For most of the Cenozoic era, open water connected the Atlantic and Pacific between North and South America. Tropical currents flowed freely through this gap, keeping the two oceans in equilibrium. Around 25 million years ago, volcanic activity began building islands in the gap as tectonic plates collided beneath Central America. Over millions of years, these islands grew, accumulated sediment between them, and gradually rose above sea level. By roughly 3–4 million years ago, the gap was fully closed. The Atlantic and Pacific were permanently separated, and North and South America were joined for the first time.",
                "details": [
                    {"key": "Span", "value": "Formed ~3–4 Ma; still exists today; Panama Canal (opened 1914) artificially reconnects the oceans"},
                    {"key": "Today", "value": "The Republic of Panama — the narrowest point of Central America, about 80 km wide"},
                ],
            },
            {
                "label": "The Great Exchange",
                "title": "The Great American Biotic Interchange",
                "body": "When the land bridge closed, tens of millions of years of separate evolution came face to face in what scientists call the Great American Biotic Interchange. From North America south: horses (which evolved entirely in North America), tapirs, llamas, deer, pumas, jaguars, and bears. From South America north: ground sloths the size of elephants, giant armadillos (glyptodonts), capybaras, and terror birds. The exchange was not equal. Most large South American native species went extinct over the following millions of years, outcompeted by North American arrivals that had been hardened by longer exposure to diverse predators and disease pressure from Eurasia.",
                "details": [
                    {"key": "Climate", "value": "Formation coincided with global cooling and onset of Pleistocene glaciation; Ice Age cycles intensified shortly after"},
                    {"key": "Life", "value": "North → South: horses, pumas, tapirs, deer. South → North: sloths, glyptodonts, capybaras. Most South American megafauna later went extinct"},
                ],
            },
            {
                "label": "The Ice Ages",
                "title": "How a land bridge triggered glaciation",
                "body": "Before the isthmus formed, warm equatorial water flowed westward from the Atlantic into the Pacific, keeping both basins in balance. When the gap closed, that equatorial exchange stopped and warm Atlantic surface water was rerouted northward — the Gulf Stream intensified dramatically. Paradoxically, a warmer North Atlantic led to more evaporation, more moisture in the atmosphere, and heavier snowfall over northern Canada and Greenland. That snow began accumulating faster than it melted. Ice sheets formed and expanded. Within a few million years the Pleistocene Ice Ages were underway — the cycle that carved the Great Lakes, built the fjords of Norway, and repeatedly reshuffled human migration across the planet.",
                "details": [
                    {"key": "Feature", "value": "Gulf Stream intensification — warm Atlantic water rerouted north, warming Europe and driving Arctic snowfall that built ice sheets"},
                    {"key": "Evidence", "value": "Marine fossils: identical shallow-water species on both sides before closure, diverging species after; mixed land mammal faunas on both continents"},
                ],
                "fun_fact": "Horses evolved in North America over 55 million years, crossed this land bridge into South America, and then went extinct in both Americas about 12,000 years ago. When Spanish conquistadors arrived in the 1500s, they were bringing horses back to the continent where the entire horse family originated.",
            },
        ],
        "quiz_question": "Why do scientists think the Isthmus of Panama's formation helped trigger the Pleistocene Ice Ages?",
        "options": [
            {"text": "The land bridge blocked cold Arctic water from flowing south into the tropics", "correct": False, "explanation": "The isthmus closed an east-west equatorial gap, not a north-south flow. The effect was redirecting warm water northward, not blocking cold water southward."},
            {"text": "It redirected warm surface water (Gulf Stream) northward, increasing Arctic snowfall that built up as permanent ice sheets", "correct": True, "explanation": "Before the isthmus, warm equatorial water flowed into the Pacific. Afterward, it was rerouted north as the Gulf Stream, increasing evaporation and snowfall over northern landmasses — snow that no longer fully melted each summer."},
            {"text": "It raised global sea levels by adding new land, which flooded low areas and cooled the planet", "correct": False, "explanation": "Land rising from the ocean slightly lowers sea levels by displacing water, not raises them. And sea level changes don't directly trigger ice ages."},
            {"text": "The volcanic activity that built the isthmus cooled the atmosphere with sulfur dioxide", "correct": False, "explanation": "Volcanic SO₂ causes short-term cooling of years to decades, not the multi-million-year trend of the Ice Ages. The sustained effect came from the ocean circulation change."},
        ],
    },
]


@login_required
def pangaea_to_now(request):
    return render(request, 'tia_core/pangaea_to_now.html', {
        'rounds_json': json.dumps(PANGAEA_TO_NOW_ROUNDS),
        'active_tab': 'play',
    })
