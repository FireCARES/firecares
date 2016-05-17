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
            template: '<div class="aster-plot"><h5 class="aster-title no-select">{{metricTitle}}</h5><svg></svg></div>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                console.log(scope, element, attrs);
                var width = 150;
                var height = 150;
                var padding = 10;
                var radius = Math.min(width - 10 - padding, height - 10 - padding) / 2;
                var innerRadius = 0.3 * radius;
                var labelr = radius + 5;

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
                        return "translate(" + ((x / h * labelr) - 3) + ',' +
                            (y / h * labelr) + ")";
                    })
                    .text(function(d) {
                        return d.data.key + 1;
                    })
                ;

                var onlySelectedArc = null;
                function mouseDownHitArc(d, i) {
                    var selected = hitArcPaths.filter('.selected');

                    if (selected[0].length === 1 && selected[0][0] === this) {
                        // Wait for a mouse up event to clear the last arc.
                        onlySelectedArc = selected[0][0];
                        return;
                    }

                    hitArcPaths.classed('selected', false);
                    dataArcPaths.classed('selected', false);
                    bgArcPaths.classed('selected', false);

                    var isSelected = d3.select(this).classed('selected');
                    d3.select(this).classed('selected', !isSelected);
                    d3.select(dataArcPaths[0][d.data.key]).classed('selected', !isSelected);
                    d3.select(bgArcPaths[0][d.data.key]).classed('selected', !isSelected);

                    var selected = hitArcPaths.filter('.selected');
                    if (selected.empty()) {
                        heatmap.resetFilter(scope.filterType);
                    } else {
                        heatmap.setFilter(scope.filterType, [d.data.key]);
                    }

                    scope.$apply();
                }

                function mouseUpHitArc(d, i) {
                    var selected = hitArcPaths.filter('.selected');
                    if (selected[0].length === 1 && selected[0][0] === onlySelectedArc) {
                        hitArcPaths.classed('selected', false);
                        dataArcPaths.classed('selected', false);
                        bgArcPaths.classed('selected', false);

                        var selected = hitArcPaths.filter('.selected');
                        if (selected.empty()) {
                            heatmap.resetFilter(scope.filterType);
                        } else {
                            heatmap.setFilter(scope.filterType, [d.data.key]);
                        }

                        scope.$apply();
                    }
                }

                var mouseButtonDown = false;
                element.on('mousedown', function() {
                    mouseButtonDown = true;
                });

                element.on('mouseup', function() {
                    mouseButtonDown = false;
                    onlySelectedArc = null;
                });

                // Handle cases where the user dragged out of the page without lifting their mouse button,
                // or other cases where they were interrupted.
                element.on('mouseenter', function() {
                    mouseButtonDown = false;
                });

                function mouseEnterHitArc(d, i) {
                    if (!mouseButtonDown) {
                        return;
                    }

                    var isSelected = d3.select(this).classed('selected');
                    d3.select(this).classed('selected', !isSelected);
                    d3.select(dataArcPaths[0][d.data.key]).classed('selected', !isSelected);
                    d3.select(bgArcPaths[0][d.data.key]).classed('selected', !isSelected);

                    if (!isSelected) {
                        heatmap.addToFilter(scope.filterType, d.data.key);
                    } else {
                        heatmap.removeFromFilter(scope.filterType, d.data.key);
                    }

                    scope.$apply();
                }

                heatmap.onRefresh(scope, function() {
                    arcScales = heatmap.totals[scope.filterType];
                    max = d3.max(arcScales, function(d) {
                        return d.value
                    });

                    // Redraw the data arcs.
                    dataArcPaths.attr("d", dataArc);
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


