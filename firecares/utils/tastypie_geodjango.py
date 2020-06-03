
def allow_geodjango_filters(model_resource_meta):
    # HACK: Tastypie has a bug where it doesn't recognize geodjango filters. The one exception is the "contains"
    # filter - but this is just a coincidental overlap with the standard string "contains" filter. So we have to
    # manually whitelist supported geodjango query terms.
    model_resource_meta.queryset.query.query_terms.update({
        'bbcontains',
        'bboverlaps',
        'contained',
        'contains',
        'contains_properly',
        'coveredby',
        'covers',
        'crosses',
        'disjoint',
        'equals',
        'intersects',
        'isvalid',
        'overlaps'
        'relate',
        'touches',
        'within',
        'left',
        'right',
        'overlaps_left',
        'overlaps_right',
        'overlaps_above',
        'overlaps_below',
        'strictly_above',
        'strictly_below',

        # Distance lookups are currently unsupported.
        # https://django-tastypie.readthedocs.io/en/v0.12.2/geodjango.html
        'distance_gt',
        'distance_gte',
        'distance_lt',
        'distance_lte',
        'dwithin',
    })
