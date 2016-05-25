'use strict';

(function() {
    angular.module('fireStation.graphs', [])
        .directive('lineChart', LineChartDirective)
        .directive('asterChart', AsterChartDirective)
        .directive('barChart', BarChartDirective)
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
                filterType: '@',
                diameter: '@',
                labelOffset: '@'
            },
            template:   '<div class="chart-header">' +
                            '<div class="chart-title">{{metricTitle}}</div>' +
                            '<span class="chart-reset no-select pull-right" ng-click="reset()">x</span>' +
                        '</div>' +
                        '<svg class="no-select"></svg>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                var diameter = (attrs.diameter) ? Number(attrs.diameter) : 175;
                var width = diameter;
                var height = diameter;
                var padding = 50;
                var radius = (diameter - padding) / 2;
                var innerRadius = 0.3 * radius;
                var labelr = radius + 10;

                if (attrs.labelOffset) {
                    labelr += Number(attrs.labelOffset);
                }

                //
                // SVG Arcs
                //
                var svg = d3.select(element).selectAll('svg')
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
                ;

                var arcData = heatmap.totals[scope.filterType];
                if (!arcData) {
                    console.error("Heatmap does not have a '" + scope.filterType + "' filter.");
                    return;
                }

                var max = d3.max(arcData, function(d) {
                    return d.value
                });

                var pie = d3.layout.pie()
                    .sort(null)
                    .value(function() {
                        return arcData.length;
                    })
                    .padAngle(.04)
                ;

                var hitPie = d3.layout.pie()
                    .sort(null)
                    .value(function() {
                        return arcData.length;
                    })
                ;

                // Background Arcs
                var bgArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(radius)
                ;

                var bgArcPaths = svg.selectAll(".chart-section-bg")
                    .data(pie(arcData))
                    .enter().append("path")
                    .attr("class", "chart-section-bg")
                    .attr("d", bgArc)
                ;

                // Foreground Arcs (data)
                var dataArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(function(d) {
                        return (radius - innerRadius) * (d.data.value / (max + (max * .1))) + innerRadius;
                    })
                ;

                var dataArcPaths = svg.selectAll(".chart-section-data")
                    .data(pie(arcData))
                    .enter().append("path")
                    .attr("class", "chart-section-data")
                    .attr("d", dataArc)
                ;

                // Hit Arcs
                var hitArcPaths = svg.selectAll(".chart-section-hit")
                    .data(hitPie(arcData))
                    .enter().append("path")
                    .attr("class", "chart-section-hit")
                    .attr("d", bgArc)
                    .on("mousedown", mouseDownHitArc)
                    .on("mouseup", mouseUpHitArc)
                    .on("mouseenter", mouseEnterHitArc)
                ;

                // Arc Labels
                svg.selectAll('.arcLabel')
                    .data(pie(arcData)).enter().append('text')
                    .attr('class', 'chart-label no-select')
                    .attr("transform", function(d) {
                        var c = bgArc.centroid(d),
                            x = c[0],
                            y = c[1],
                            h = Math.sqrt(x * x + y * y);
                        return "translate(" + ((x / h * labelr)) + ',' +
                            (y / h * labelr) + ")";
                    })
                    .attr('text-anchor', 'middle')
                    .attr('alignment-baseline', 'central')
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
                    if (d.data.value == 0) {
                        return;
                    }

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

                    if (d.data.value == 0) {
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
                    arcData = heatmap.totals[scope.filterType];
                    max = d3.max(arcData, function(d) {
                        return d.value
                    });

                    for (var i = 0; i < dataArcPaths[0].length; i++) {
                        var arcPath = d3.select(dataArcPaths[0][i]);
                        var nextD = dataArc(arcPath.data()[0]);
                        arcPath.attr('nextD', nextD);
                    }

                    // Animate the data arcs to their new size.
                    dataArcPaths.transition()
                        .duration(500)
                        .ease('cubic-out')
                        .attrTween("d", arcTween); // redraw the arcs

                    function arcTween(next) {
                        var dataArc = d3.select(this);
                        var curD = SVGArcStrToArray(dataArc.attr('d'));
                        var nextD = SVGArcStrToArray(dataArc.attr('nextD'));
                        var interp = d3.interpolate(curD, nextD);
                        return function(t) {
                            return SVGArcArrayToStr(interp(t));
                        };
                    }
                });

                heatmap.onFilterChanged(scope.filterType, scope, function(ev, filter) {
                    // Deselect all arcs.
                    bgArcPaths.classed('selected', false);
                    dataArcPaths.classed('selected', false);
                    hitArcPaths.classed('selected', false);

                    // Reselect the active ones.
                    for (var i = 0; i < filter.length; i++) {
                        var key = filter[i];
                        d3.select(bgArcPaths[0][key]).classed('selected', true);
                        d3.select(dataArcPaths[0][key]).classed('selected', true);
                        d3.select(hitArcPaths[0][key]).classed('selected', true);
                    }
                });
            }
        };
    }


    BarChartDirective.$inject = ['heatmap'];

    function BarChartDirective(heatmap) {
        return {
            restrict: 'CE',
            replace: false,
            scope: {
                metricTitle: '@?',
                filterType: '@',
                width: '@',
                height: '@',
                maxYears: '@'
            },
            template:   '<div class="chart-header">' +
                            '<div class="chart-title">{{metricTitle}}</div>' +
                            '<span class="chart-reset no-select pull-right" ng-click="reset()">x</span>' +
                        '</div>' +
                        '<svg class="no-select"></svg>',
            // The linking function will add behavior to the template
            link: function(scope, element, attrs) {
                var width = (attrs.width) ? Number(attrs.width) : element[0].parentElement.offsetWidth;
                var height = (attrs.height) ? Number(attrs.height) : 150;
                var maxYears = (attrs.maxYears) ? Number(attrs.maxYears) : 8;
                var scaleSteps = 5;

                var svg = d3.select(element).selectAll('svg')
                    .attr("width", width)
                    .attr("height", height)
                ;

                var svgBarGroup = svg.append('g')
                    .attr('class', 'bar-chart-bars')
                ;

                var svgLabelGroup = svg.append('g')
                    .attr('class', 'bar-chart-labels')
                ;

                var barData = heatmap.totals[scope.filterType];
                if (!barData) {
                    console.error("Heatmap does not have a '" + scope.filterType + "' filter.");
                    return;
                }

                var availableYears = Math.floor(barData.length / 12);
                var years = Math.min(availableYears, maxYears);

                function calculateMax() {
                    var rawMax = d3.max(barData, function(d) {
                        return d.value
                    });

                    // Make sure our max breaks up into even parts for the scale.
                    var multiple = scaleSteps - 1;
                    if (rawMax > (multiple * 200)) {
                        multiple *= 50;
                    } else if (rawMax > (multiple * 100)) {
                        multiple *= 25;
                    } else if (rawMax > (multiple * 50)) {
                        multiple *= 10;
                    } else if (rawMax > (multiple * 25)) {
                        multiple *= 5;
                    } else {
                        multiple *= 2;
                    }

                    return Math.ceil(rawMax / multiple) * multiple;
                }

                // NOTE: Because the SVG Y axis is top down, we have to flip the Y axis and reverse
                //       the Y positioning of elements in order to get the bars animating correctly.
                //       As a result, the vertical positioning math may be slightly counterintuitive.

                // Create a bar for each month, for as many years as we're displaying.
                var bgBars = [];
                var dataBars = [];
                var hitBars = [];
                var keyToIndex = {};
                var keyToData = {};
                var leftPadding = 25;
                var bottomPadding = 25;
                var totalBarWidth = width - leftPadding;
                var maxBarHeight = height - bottomPadding;
                var numBars = years * 12;
                var barPadding = 2;
                var barWidth = totalBarWidth / numBars - barPadding;
                var max = calculateMax();
                for (var i = 0; i < numBars; i++) {
                    var data = barData[barData.length - 1 - i];
                    var barHeight = (data.value / (max + (max * .1))) * maxBarHeight;
                    var bgBar = svgBarGroup.append('rect')
                        .attr('class', 'chart-section-bg')
                        .attr('x', leftPadding + totalBarWidth - i * (barWidth + barPadding) - barWidth - barPadding)
                        .attr('y', bottomPadding)
                        .attr('width', barWidth)
                        .attr('height', maxBarHeight)
                    ;

                    bgBars.push(bgBar);

                    var dataBar = svgBarGroup.append('rect')
                        .attr('class', 'chart-section-data')
                        .attr('x', leftPadding + totalBarWidth - i * (barWidth + barPadding) - barWidth - barPadding)
                        .attr('y', bottomPadding)
                        .attr('width', barWidth)
                        .attr('height', barHeight)
                    ;

                    dataBars.push(dataBar);

                    var hitBar = svgBarGroup.append('rect')
                        .attr('class', 'chart-section-hit')
                        .attr('x', leftPadding + totalBarWidth - i * (barWidth + barPadding) - barWidth - barPadding)
                        .attr('y', bottomPadding)
                        .attr('width', barWidth + barPadding)
                        .attr('height', maxBarHeight)
                        .attr('key', data.key)
                        .on('mousedown', mouseDownHitBar)
                        .on('mouseup', mouseUpHitBar)
                        .on('mouseenter', mouseEnterHitBar)
                    ;

                    hitBars.push(hitBar);

                    keyToIndex[data.key] = i;
                    keyToData[data.key] = data;
                }

                // Year labels.
                var yearWidth = (barWidth + barPadding) * 12;
                for (i = 0; i < years; i++) {
                    var x = width - i * yearWidth - yearWidth;
                    if (x < 0) {
                        continue;
                    }

                    var key = barData[barData.length - 1 - i * 12].key;
                    var yearText = key.split('-')[0];
                    svgLabelGroup.append('text')
                        .attr('class', 'chart-label')
                        .attr('x', x)
                        .attr('y', 15 - bottomPadding)
                        .attr('dx', 0)
                        .attr('dy', 0)
                        .text(yearText)
                }

                // Scale labels.
                var scaleLabels = [];
                var scaleStep = max / (scaleSteps - 1);
                for (i = 0; i < scaleSteps; i++) {
                    var scaleValue = Math.ceil(scaleStep * i);
                    var scaleLabel = svgLabelGroup.append('text')
                        .attr('class', 'chart-label')
                        .attr('x', 18)
                        .attr('y', -i * (maxBarHeight / (scaleSteps - 1) - 2) - bottomPadding)
                        .attr('dx', 0)
                        .attr('dy', 0)
                        .attr('text-anchor', 'end')
                        .text(scaleValue.toLocaleString())
                    ;

                    scaleLabels.push(scaleLabel);
                }

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
                function mouseDownHitBar(d, i) {
                    var key = d3.select(this).attr('key');

                    var data = keyToData[key];
                    if (data.value == 0) {
                        return;
                    }

                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(key) !== -1) {
                        // Wait for a mouse up event to clear the last arc.
                        onlyFilteredKey = key;
                        return;
                    }

                    heatmap.setFilter(scope.filterType, [key]);
                }

                function mouseUpHitBar(d, i) {
                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(onlyFilteredKey) !== -1) {
                        heatmap.resetFilter(scope.filterType);
                    }
                }

                function mouseEnterHitBar(d, i) {
                    if (!mouseButtonDown) {
                        return;
                    }

                    var key = d3.select(this).attr('key');

                    data = keyToData[key];
                    if (data.value == 0) {
                        return;
                    }

                    heatmap.toggle(scope.filterType, key);
                }

                scope.reset = function() {
                    heatmap.resetFilter(scope.filterType);
                };

                //
                // Heatmap events
                //
                heatmap.onRefresh(scope, function() {
                    // Calculate the max bar scale.
                    barData = heatmap.totals[scope.filterType];
                    max = calculateMax();

                    // Animate to the new bar heights.
                    for (var i = 0; i < dataBars.length; i++) {
                        var value = barData[barData.length - 1 - i].value;
                        dataBars[i].attr('nextHeight', (value / (max + (max * .1))) * maxBarHeight);

                        dataBars[i].transition()
                            .duration(500)
                            .ease('cubic-out')
                            .attrTween('height', barTween)
                        ;
                    }

                    function barTween() {
                        var dataBar = d3.select(this);
                        var curHeight = dataBar.attr('height');
                        var nextHeight = dataBar.attr('nextHeight');
                        var interp = d3.interpolate(curHeight, nextHeight);
                        return function(t) {
                            return interp(t);
                        }
                    }

                    // Update scale labels.
                    scaleStep = max / (scaleSteps - 1);
                    for (i = 0; i < scaleSteps; i++) {
                        var scaleValue = Math.ceil(scaleStep * i);
                        scaleLabels[i].text(scaleValue.toLocaleString());
                    }
                });

                var bgBarSelection = svg.selectAll('.chart-section-bg');
                var dataBarSelection = svg.selectAll('.chart-section-data');
                var hitBarSelection = svg.selectAll('.chart-section-hit');
                heatmap.onFilterChanged(scope.filterType, scope, function(ev, filter) {
                    // Deselect all bars.
                    bgBarSelection.classed('selected', false);
                    dataBarSelection.classed('selected', false);
                    hitBarSelection.classed('selected', false);

                    // Reselect the active ones.
                    for (var i = 0; i < filter.length; i++) {
                        var index = keyToIndex[filter[i]];
                        bgBars[index].classed('selected', true);
                        dataBars[index].classed('selected', true);
                        hitBars[index].classed('selected', true);
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

    //
    // Helper functions
    //

    // Convert SVG arc 'd' string to an array of commands.
    // https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
    function SVGArcStrToArray(str) {
        // Chop closing 'Z' command at the end.
        str = str.substring(0, str.length - 1);

        var cmds = str.split(/(?=[LMA])/);

        var array = [];
        for (var i = 0; i < cmds.length; i++) {
            var cmdStr = cmds[i];
            var cmd = {};
            cmd.type = cmdStr.charAt(0);
            cmd.values = [];

            // Remove 'type' character from start of cmd string.
            cmdStr = cmdStr.substring(1);

            // Command values come in a two dimensional array, dilineated by ' ' and ','.
            var cmdStrNums = cmdStr.split(' ');
            for (var j = 0; j < cmdStrNums.length; j++) {
                var numStrs = cmdStrNums[j].split(',');
                var nums = [];
                for (var k = 0; k < numStrs.length; k++) {
                    nums.push(Number(numStrs[k]));
                }

                cmd.values.push(nums);
            }

            array.push(cmd);
        }

        return array;
    }

    // Convert arc SVG array of commands back to 'd' string.
    function SVGArcArrayToStr(array) {
        var str = '';
        for (var i = 0; i < array.length; i++) {
            var section = array[i];
            str += section.type;

            var valuesStrArray = [];
            for (var j = 0; j < section.values.length; j++) {
                valuesStrArray.push(section.values[j].join(','));
            }

            str += valuesStrArray.join(' ');
        }

        // Add closing 'Z' command.
        str += 'Z';

        return str;
    }
}());


