'use strict';

(function() {
    angular.module('fireStation.graphs', [])
        .directive('lineChart', LineChartDirective)
        .directive('asterChart', AsterChartDirective)
        .directive('bulletChart', BulletChartDirective)
    ;

    function LineChartDirective() {
        return {
            restrict: 'CE',
            replace: false,
            scope: {
                metricTitle: '@?',
                description: '@?',
                xaxisLabel: '@?',
                yaxisLabel: '@?',
                data: '=',
                color: '@',
                value: '@?'
            },
            template: '<svg></svg><div class="metric-description"><h4>{[metricTitle]}</h4><p>{[description]}</p></div>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                var id = element.attr('id');
                var chartElement = '#' + id + ' svg';

                function data() {

                    return [{
                        values: scope.data,
                        color: scope.color
                    }];
                }

                nv.addGraph(function() {
                    var chart = nv.models.lineChart()
                        .useInteractiveGuideline(true)
                        .showLegend(false)
                        .useInteractiveGuideline(false)
                        .showXAxis(true)
                        .showYAxis(true)
                        .x(function(d) {
                            return d[0]
                        })
                        .y(function(d) {
                            return d[1]
                        })
                        .interpolate('basis');

                    chart.xAxis
                        .axisLabel(scope.xaxisLabel)
                        .tickFormat(d3.format(',r'))
                    ;

                    chart.yAxis
                        .axisLabel(scope.yaxisLabel)
                        .tickFormat(d3.format('.00f'))
                    ;

                    d3.select(chartElement)
                        .datum(data(), function(d) {
                            return d[0]
                        })
                        .transition().duration(500)
                        .call(chart);

                    var hit = false;

                    function firstHit(value) {
                        if (hit === true) {
                            return false;
                        } else if (value >= scope.value) {
                            hit = true;
                            return true;
                        }
                    }

                    if (scope.value != null) {
                        // add the locator point
                        var chartNode = d3.select(chartElement)
                        var chartNodeData = chartNode.datum()[0];
                        chartNode.select('.nv-groups')
                            .selectAll("circle.valueLocation")
                            .data(chartNodeData.values.filter(function(d) {
                                return firstHit(d[0])
                            }))
                            .enter().append("circle").attr("class", "metric-value-location")
                            .attr("cx", function(d) {
                                return chart.xAxis.scale()(d[0]);
                            })
                            .attr("cy", function(d) {
                                return chart.yAxis.scale()(d[1]);
                            })
                            .attr("r", 4);
                    }

                    nv.utils.windowResize(chart.update);
                    return chart;

                });
            }
        };
    }


    AsterChartDirective.$inject = ['heatmap'];

    function AsterChartDirective(heatmap) {
        return {
            restrict: 'CE',
            replace: false,
            scope: {
                metricTitle: '@?',
                description: '@?',
                filterType: '@'
            },
            template:   '<div class="aster-plot">' +
                            '<div class="aster-header">' +
                                '<div class="aster-title">{{metricTitle}}</div>' +
                                '<span class="aster-reset pull-right" ng-click="reset()">x</span>' +
                            '</div>' +
                            '<svg class="no-select"></svg>' +
                        '</div>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                console.log(scope, element, attrs);
                var width = 175;
                var height = 175;
                var padding = 25;
                var radius = Math.min(width - 10 - padding, height - 10 - padding) / 2;
                var innerRadius = 0.3 * radius;
                var labelr = radius + 10;

                //
                // SVG Arcs
                //
                var svg = d3.select(element).selectAll('svg')
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
                ;

                var arcScales = heatmap.totals[scope.filterType];
                var max = d3.max(arcScales, function(d) {
                    return d.value
                });

                var pie = d3.layout.pie()
                    .sort(null)
                    .value(function() {
                        return arcScales.length;
                    })
                    .padAngle(.04)
                ;

                // Background Arcs
                var bgArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(radius)
                ;

                var bgArcPaths = svg.selectAll(".bgArc")
                    .data(pie(arcScales))
                    .enter().append("path")
                    .attr("class", "bgArc")
                    .attr("d", bgArc)
                ;

                // Foreground Arcs (data)
                var dataArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(function(d) {
                        return (radius - innerRadius) * (d.data.value / (max + (max * .1))) + innerRadius;
                    })
                ;

                var dataArcPaths = svg.selectAll(".dataArc")
                    .data(pie(arcScales))
                    .enter().append("path")
                    .attr("class", "dataArc")
                    .attr("d", dataArc)
                ;

                // Hit Arcs
                var hitArcPaths = svg.selectAll(".hitArc")
                    .data(pie(arcScales))
                    .enter().append("path")
                    .attr("class", "hitArc")
                    .attr("d", bgArc)
                    .on("mousedown", mouseDownHitArc)
                    .on("mouseup", mouseUpHitArc)
                    .on("mouseenter", mouseEnterHitArc)
                ;

                // Arc Labels
                svg.selectAll('.arcLabel')
                    .data(pie(arcScales)).enter().append('text')
                    .attr('class', 'aster-label no-select')
                    .attr("dy", ".35em")
                    .attr("transform", function(d) {
                        var c = bgArc.centroid(d),
                            x = c[0],
                            y = c[1],
                            h = Math.sqrt(x * x + y * y);
                        return "translate(" + ((x / h * labelr) - 4) + ',' +
                            (y / h * labelr) + ")";
                    })
                    .text(function(d) {
                        var labels = heatmap.labels[scope.filterType];
                        if (labels) {
                            return labels[d.data.key];
                        } else {
                            return d.data.key + 1;
                        }
                    })
                ;

                //
                // Input
                //
                var mouseButtonDown = false;
                element.on('mousedown', function() {
                    mouseButtonDown = true;
                });

                element.on('mouseup', function() {
                    mouseButtonDown = false;
                    onlyFilteredKey = -1;
                });

                // Handle cases where the user dragged out of the page without lifting their mouse button,
                // or other cases where they were interrupted.
                element.on('mouseenter', function() {
                    mouseButtonDown = false;
                });

                var onlyFilteredKey = -1;
                function mouseDownHitArc(d, i) {
                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(d.data.key) !== -1) {
                        // Wait for a mouse up event to clear the last arc.
                        onlyFilteredKey = d.data.key;
                        return;
                    }

                    heatmap.setFilter(scope.filterType, [d.data.key]);
                }

                function mouseUpHitArc(d, i) {
                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(onlyFilteredKey) !== -1) {
                        heatmap.resetFilter(scope.filterType);
                    }
                }

                function mouseEnterHitArc(d, i) {
                    if (!mouseButtonDown) {
                        return;
                    }

                    heatmap.toggle(scope.filterType, d.data.key);
                }

                scope.reset = function() {
                    heatmap.resetFilter(scope.filterType);
                };

                //
                // Heatmap events
                //
                heatmap.onRefresh(scope, function() {
                    // Calculate the max arc scale.
                    arcScales = heatmap.totals[scope.filterType];
                    max = d3.max(arcScales, function(d) {
                        return d.value
                    });

                    // Redraw the data arcs.
                    dataArcPaths.attr("d", dataArc);
                });

                heatmap.onFilterChanged(scope.filterType, scope, function(ev, filter) {
                    // Deselect all arcs.
                    hitArcPaths.classed('selected', false);
                    dataArcPaths.classed('selected', false);
                    bgArcPaths.classed('selected', false);

                    // Reselect the active ones.
                    for (var i = 0; i < filter.length; i++) {
                        var key = filter[i];
                        d3.select(hitArcPaths[0][key]).classed('selected', true);
                        d3.select(dataArcPaths[0][key]).classed('selected', true);
                        d3.select(bgArcPaths[0][key]).classed('selected', true);
                    }
                });
            }
        };
    }

    function BulletChartDirective() {
        return {
            restrict: 'CE',
            replace: false,
            scope: {
                metricTitle: '@?',
                description: '@?',
                ranges: '=',
                measures: '=',
                markers: '='
            },
            template: '<div class="metric-description ct-u-marginBottom20"><h4>{[metricTitle]}</h4></div><svg></svg><div class="metric-description"><p>{[description]}</p></div>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                var id = element.attr('id');
                var chartElement = '#' + id + ' svg';
                // ranges are the background
                // measures are the middle line
                // markers are the vertical line
                scope.data = [{"ranges": scope.ranges, "measures": scope.measures, "markers": scope.markers}];


                var margin = {top: 5, right: 40, bottom: 20, left: 10},
                    width = 300 - margin.left - margin.right,
                    height = 40 - margin.top - margin.bottom;

                var chart = d3.bullet()
                    .width(width)
                    .height(height);

                var svg = d3.select(chartElement).selectAll("svg")
                    .data(scope.data)
                    .enter().append("svg")
                    .attr("class", "bullet")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
                    .call(chart);
            }
        };
    }
}());


