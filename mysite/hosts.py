from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', 'mysite.urls', name='www'),
    host(r'myunclethetrex', 'myunclethetrex.urls', name='myunclethetrex'),
    host(r'tempesttoday', 'tempesttoday.urls', name='tempesttoday'),
    host(r'beingneighborly', 'beingneighborly.urls', name='beingneighborly'),
    host(r'', 'mysite.urls', name='main'),
)
