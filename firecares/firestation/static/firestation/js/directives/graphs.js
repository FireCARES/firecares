'use strict';

(function() {
    angular.module('fireStation.graphs', [])
        .directive('lineChart', LineChartDirective)
        .directive('asterChart', AsterChartDirective)
        .directive('barChart', BarChartDirective)
        .directive('bulletChart', BulletChartDirective)
        .directive('riskDistributionBarChart', RiskDistributionBarChartDirective)
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

                var labels = heatmap.labels[scope.filterType];
                if (!labels) {
                    console.error("No labels found for '" + scope.filterType + "' filter.");
                    return;
                }

                var arcData = heatmap.totals[scope.filterType];
                if (!arcData) {
                    console.error("Heatmap does not have a '" + scope.filterType + "' filter.");
                    return;
                }

                var max = d3.max(arcData, function(d) { return d.value });

                // Fill in any gaps in the data with zeroed dummy entries.
                var missingKeys = [];
                for (var i = 0; i < labels.length; i++) {
                    missingKeys.push(i);
                }

                for (i = 0; i < arcData.length; i++) {
                    var arcKey = arcData[i].key;
                    missingKeys.splice(missingKeys.indexOf(arcKey), 1);
                }

                for (i = 0; i < missingKeys.length; i++) {
                    arcData.push({
                        key: missingKeys[i],
                        value: 0
                    });
                }

                arcData.sort(function(a, b) { return a.key - b.key; });

                //
                // SVG Arcs
                //
                var svg = d3.select(element).selectAll('svg')
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
                ;

                var pie = d3.layout.pie()
                    .sort(null)
                    .value(function() { return labels.length; })
                    .padAngle(.04)
                ;

                var hitPie = d3.layout.pie()
                    .sort(null)
                    .value(function() { return labels.length; })
                ;

                var pathSortByKey = function(a, b) {
                    var dataA = d3.select(a).data()[0];
                    var dataB = d3.select(b).data()[0];
                    return dataA.data.key - dataB.data.key;
                };

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

                bgArcPaths[0].sort(pathSortByKey);

                // Foreground Arcs (data)
                var maxPaddingScale = .075;
                var dataArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(function(d) {
                        var value = d.data.value || 0;
                        var scale = (max) ? (value / (max + (max * maxPaddingScale))) : 0;
                        return (radius - innerRadius) * scale + innerRadius;
                    })
                ;

                var dataArcPaths = svg.selectAll(".chart-section-data")
                    .data(pie(arcData))
                    .enter().append("path")
                    .attr("class", "chart-section-data")
                    .attr("d", dataArc)
                ;

                dataArcPaths[0].sort(pathSortByKey);

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

                hitArcPaths[0].sort(pathSortByKey);

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
                        return labels[d.data.key];
                    })
                ;

                //
                // Input
                //
                var mouseButtonDown = false;
                var lastArcKey = -1;
                var mouseDownArcIndex = -1;
                var selectDirection = 0;
                var selectedIndices = [];

                element.on('mouseup', function() {
                    mouseButtonDown = false;
                    lastArcKey = -1;
                    mouseDownArcIndex = -1;
                    selectDirection = 0;
                });

                // Handle cases where the user dragged out of the page without lifting their mouse button,
                // or other cases where they were interrupted.
                element.on('mouseenter', function() {
                    mouseButtonDown = false;
                });

                function mouseDownHitArc(d, i) {
                    if (d.data.value == 0) {
                        return;
                    }

                    mouseDownArcIndex = d.data.key;
                    selectedIndices = [mouseDownArcIndex];
                    mouseButtonDown = true;

                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(d.data.key) !== -1) {
                        // Wait for a mouse up event to clear the last arc.
                        lastArcKey = d.data.key;
                        return;
                    }

                    heatmap.setFilter(scope.filterType, [d.data.key]);
                }

                function mouseUpHitArc(d) {
                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(lastArcKey) !== -1) {
                        heatmap.resetFilter(scope.filterType);
                    }
                }

                function mouseEnterHitArc(d) {
                    if (!mouseButtonDown) {
                        return;
                    }

                    // Ignore empty arcs.
                    if (d.data.value == 0) {
                        return;
                    }

                    // Reset the flag for the last arc toggle on mouse up.
                    lastArcKey = -1;

                    var index = hitArcPaths[0].indexOf(this);

                    // For the first multi-selection, determine the direction we're most likely trying to select in.
                    // Once the direction has been decided, keep selecting in that direction until we revert back
                    // to a single selection. Then start the process over again.
                    if (index === mouseDownArcIndex) {
                        selectDirection = 0;
                    } else if (selectDirection === 0) {
                        // Clockwise.
                        var distanceCW = 0;
                        var testIndex = mouseDownArcIndex;
                        while (distanceCW < hitArcPaths[0].length) {
                            testIndex++;
                            distanceCW++;

                            if (testIndex >= hitArcPaths[0].length) {
                                testIndex = 0;
                            }

                            if (testIndex === index) {
                                break;
                            }
                        }

                        // Counter clockwise.
                        var distanceCCW = 0;
                        testIndex = mouseDownArcIndex;
                        while (distanceCCW < hitArcPaths[0].length) {
                            testIndex--;
                            distanceCCW++;

                            if (testIndex < 0) {
                                testIndex = hitArcPaths[0].length - 1;
                            }

                            if (testIndex === index) {
                                break;
                            }
                        }

                        if (distanceCCW < distanceCW) {
                            selectDirection = -1;
                        } else {
                            selectDirection = 1;
                        }
                    }

                    // Choose the selected indices based on our select direction.
                    selectedIndices = [];
                    var select = mouseDownArcIndex;
                    selectedIndices.push(select);
                    while (select !== index) {
                        select += selectDirection;

                        // Loop the indices.
                        if (select >= hitArcPaths[0].length) {
                            select = 0;
                        } else if (select < 0) {
                            select = hitArcPaths[0].length - 1;
                        }

                        selectedIndices.push(select);
                    }

                    // Convert indices to keys and update the filter.
                    var keys = [];
                    for (var i = 0; i < selectedIndices.length; i++) {
                        var selectedIndex = selectedIndices[i];
                        var path = d3.select(hitArcPaths[0][selectedIndex]);
                        var data = path.data()[0];
                        keys.push(data.data.key);
                    }

                    heatmap.setFilter(scope.filterType, keys);
                }

                scope.reset = function() {
                    selectedIndices = [];
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

                    // Use data binding to avoid use of path to array conversions
                    dataArcPaths.data(pie(arcData))
                        .transition()
                        .duration(500)
                        .ease('cubic-out')
                        .attr("d", dataArc)
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

    function RiskDistributionBarChartDirective() {
      return {
        restrict: 'CE',
        replace: false,
        scope: {
          metricTitle: '@?',
          width: '@',
          height: '@',
          low: '@',
          medium: '@',
          high: '@',
          unknown: '@'
        },
        template: '<svg class="no-select"></svg>',
        link: function(scope, element, attrs) {
          element.find('svg').appear(function() {
            var width = parseInt(attrs.width);
            var height = parseInt(attrs.height);
            var margins = {top: 0, left: 60, right: 0, bottom: 20};

            var data = [{
                'level': 'Low',
                'value': parseInt(attrs.low || 0)
              },{
                'level': 'Medium',
                'value': parseInt(attrs.medium || 0)
              },{
                'level': 'High',
                'value': parseInt(attrs.high || 0)
              },{
                'level': 'Unknown',
                'value': parseInt(attrs.unknown || 0)
              }];

            var svg = d3.select(element).selectAll('svg')
              .attr("width", width + margins.left + margins.right)
              .attr("height", height + margins.top + margins.bottom)
              .append('g')
              .attr('transform', 'translate(' + margins.left + ',' + margins.top + ')');

            var svgBarGroup = svg.append('g').attr('class', 'bar-chart-bars').attr('transform', 'translate(5,0)');

            var svgLabelGroup = svg.append('g').attr('class', 'bar-chart-labels');

            var tip = d3.tip()
              .attr('class', 'd3-tip')
              .offset([-10, 0])
              .html(function(d) {
                return "<strong>Structure count:</strong> <span class='tip-value'>" + humanizeInteger(d.value) + "</span>";
              });

            svg.call(tip);

            var x = d3.scale.ordinal().rangeRoundBands([0, width], .5);
            var y = d3.scale.linear().range([height, 0]);

            x.domain(_.pluck(data, 'level'));
            y.domain([0, d3.max(_.pluck(data, 'value'))]);

            var idx = 0;
            var keyCount = Object.keys(data).length;

            svgBarGroup.selectAll('.chart-section-data')
                .data(data)
              .enter()
                .append('rect')
                .attr('class', 'chart-section-data')
                .attr('x', function(d) { return x(d.level) - margins.left / 3; })
                .attr('y', height)
                .attr('width', x.rangeBand())
                .attr('height', 0)
                .on('mouseover', tip.show)
                .on('mouseout', tip.hide)
                .transition()
                  .duration(1000)
                  .ease('cubic-out')
                  .attr('height', function(d) { return height - y(d.value); })
                  .attr('y', function(d) { return y(d.value); });

            var xAxis = d3.svg.axis().scale(x).orient('bottom').tickSize(0);
            var yAxis = d3.svg.axis().scale(y).orient('left').ticks(4);

            svg.append('g')
                .attr('class', 'x axis')
                .attr('transform', 'translate(' + (-(margins.left / 3) + 5) + ',' + (height + 5) + ')')
                .call(xAxis);

            svg.append('g')
              .attr('class', 'y axis')
              .call(yAxis);
          });
        }
      }
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

                // Override transform attribute to fix IE text flip.
                svgLabelGroup.attr('transform', 'scale(1, -1)')

                var barData = heatmap.totals[scope.filterType];
                if (!barData) {
                    console.error("Heatmap does not have a '" + scope.filterType + "' filter.");
                    return;
                }

                var latestYear = new Date(barData[barData.length - 1].key).getFullYear();
                var oldestYear = new Date(barData[0].key).getFullYear();
                var yearSpan = latestYear - oldestYear;
                var years = Math.min(yearSpan, maxYears);

                barData = normalizedBarData(barData);

                function normalizedBarData(barData) {
                    // Fill in any gaps in the data with zeroed dummy entries.
                    var barDataByKey = {};
                    for (i = 0; i < barData.length; i++) {
                        barDataByKey[barData[i].key] = barData[i];
                    }

                    var oldestVisibleYear = latestYear - years + 1;
                    var results = [];
                    for (var year = oldestVisibleYear; year <= latestYear; year++) {
                        for (var month = 0; month < 12; month++) {
                            var key = heatmap.keyForYearsMonths(year, month);
                            var existingData = barDataByKey[key];
                            var value = (existingData) ? existingData.value : 0;
                            results.push({
                                key: key,
                                value: value
                            });
                        }
                    }

                    return results;
                }

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
                var barPadding = 2;
                var barWidth = totalBarWidth / barData.length - barPadding;
                var max = calculateMax();
                for (var i = 0; i < barData.length; i++) {
                    var data = barData[barData.length - 1 - i];
                    var bgBar = svgBarGroup.append('rect')
                        .attr('class', 'chart-section-bg')
                        .attr('x', leftPadding + totalBarWidth - i * (barWidth + barPadding) - barWidth - barPadding)
                        .attr('y', bottomPadding)
                        .attr('width', barWidth)
                        .attr('height', maxBarHeight)
                        .attr('key', data.key)
                    ;

                    bgBars.push(bgBar);

                    var barHeight = (max) ? ((data.value / max) * maxBarHeight) : 0;
                    var dataBar = svgBarGroup.append('rect')
                        .attr('class', 'chart-section-data')
                        .attr('x', leftPadding + totalBarWidth - i * (barWidth + barPadding) - barWidth - barPadding)
                        .attr('y', bottomPadding)
                        .attr('width', barWidth)
                        .attr('height', barHeight)
                        .attr('key', data.key)
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
                var lastBarKey = -1;
                var mouseDownBarIndex = -1;
                var selectedIndices = [];

                element.on('mouseup', function() {
                    mouseButtonDown = false;
                    lastBarKey = -1;
                    mouseDownBarIndex = -1;
                });

                // Handle cases where the user dragged out of the page without lifting their mouse button,
                // or other cases where they were interrupted.
                element.on('mouseenter', function() {
                    mouseButtonDown = false;
                    lastBarKey = -1;
                    mouseDownBarIndex = -1;
                });

                function mouseDownHitBar(d, i) {
                    var key = d3.select(this).attr('key');

                    var data = keyToData[key];
                    if (data.value == 0) {
                        return;
                    }

                    mouseDownBarIndex = keyToIndex[key];
                    selectedIndices = [mouseDownBarIndex];
                    mouseButtonDown = true;

                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(key) !== -1) {
                        // Wait for a mouse up event to clear the last arc.
                        lastBarKey = key;
                        return;
                    }

                    heatmap.setFilter(scope.filterType, [key]);
                }

                function mouseUpHitBar(d) {
                    var filter = heatmap.filters[scope.filterType];
                    if (filter.length === 1 && filter.indexOf(lastBarKey) !== -1) {
                        heatmap.resetFilter(scope.filterType);
                    }
                }

                function mouseEnterHitBar(d) {
                    if (!mouseButtonDown) {
                        return;
                    }

                    var key = d3.select(this).attr('key');

                    // Ignore empty bars.
                    data = keyToData[key];
                    if (data.value == 0) {
                        return;
                    }

                    // Select a contiguous range between the bar we're dragging from and the bar we're currently over.
                    var index = keyToIndex[key];
                    selectedIndices = [mouseDownBarIndex];
                    if (index !== mouseDownBarIndex) {
                        var selectDirection = (index > mouseDownBarIndex) ? 1 : -1;
                        var select = mouseDownBarIndex;
                        while (select !== index) {
                            select += selectDirection;
                            selectedIndices.push(select);
                        }
                    }

                    // Convert indices to keys and update the filter.
                    var keys = [];
                    for (var i = 0; i < selectedIndices.length; i++) {
                        var selectedIndex = selectedIndices[i];
                        keys.push(hitBars[selectedIndex].attr('key'));
                    }

                    heatmap.setFilter(scope.filterType, keys);
                }

                scope.reset = function() {
                    selectedIndices = [];
                    heatmap.resetFilter(scope.filterType);
                };

                //
                // Heatmap events
                //
                heatmap.onRefresh(scope, function() {
                    barData = normalizedBarData(heatmap.totals[scope.filterType]);
                    max = calculateMax();

                    // Animate to the new bar heights.
                    for (var i = 0; i < dataBars.length; i++) {
                        var value = barData[barData.length - 1 - i].value;
                        var nextBarHeight = (max) ? ((value / max) * maxBarHeight) : 0;
                        dataBars[i].attr('nextHeight', nextBarHeight);

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

                        // HACK: It's possible to select bars farther back than the shorter mobile chart displays.
                        //       Just ignore invalid indices for now. Ideally, we should only have one chart that
                        //       dynamically resizes based on the screen size.
                        if (!index) {
                            continue;
                        }

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
}());
