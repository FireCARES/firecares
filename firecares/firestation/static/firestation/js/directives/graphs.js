'use strict';

(function() {
  var module = angular.module('fireStation.graphs', []);

  module.directive('lineChart',
      function() {
        return {
          restrict: 'CE',
          replace: false,
          scope: {
             metricTitle: '@?',
             description: '@?',
             xaxisLabel: '@?',
             yaxisLabel: '@?',
             data:'=',
             color: '@',
             value: '@?'
          },
          template: '<svg></svg><div class="metric-description"><h4>{[metricTitle]}</h4><p>{[description]}</p></div>',
          // The linking function will add behavior to the template
          link: function(scope, element, attrs) {
              var id = element.attr('id');
              var chartElement =  '#' + id + ' svg';

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
                    .x(function(d) { return d[0] })
                    .y(function(d) { return d[1] })
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
                    .datum(data(), function (d){ return d[0]})
                    .transition().duration(500)
                    .call(chart);

                  var hit = false;
                  function firstHit(value) {
                      if (hit===true) {
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
                        .data(chartNodeData.values.filter(function(d){return firstHit(d[0])}))
                        .enter().append("circle").attr("class", "metric-value-location")
                        .attr("cx", function(d) { return chart.xAxis.scale()(d[0]); })
                        .attr("cy", function(d) { return chart.yAxis.scale()(d[1]); })
                        .attr("r", 4);
                  }

                  nv.utils.windowResize(chart.update);
                  return chart;

                });
          }
        };
      });


  module.directive('asterChart',
      function() {
        return {
          restrict: 'CE',
          replace: false,
          scope: {
             metricTitle: '@?',
             description: '@?',
             //array of objects with key, values
             data: '=',
             crossfilter: '&',
             filterType: '@'
          },
          template: '<div class="aster-plot"><h5 class="aster-title">{{metricTitle}}</h5><svg></svg></div>',
          // The linking function will add behavior to the template
          link: function(scope, element, attrs) {
              console.log(scope, element, attrs);
              var id = attrs.id;
              var width = 125,
                height = 125,
                padding = 10,
                radius = Math.min(width-10-padding, height-10-padding) / 2,
                innerRadius = 0.3 * radius,
                max = d3.max(scope.data, function(d){return d.value}),
                labelr = radius + 5,
                element = element,
                dragging;

              scope.filters = [];

            scope.$watchCollection('filters', function(newValue, oldValue) {
                console.log('--Querying with new filters: ', newValue);
                var hits = scope.crossfilter().filter(null);

                if (newValue.length > 0) {
                 hits = scope.crossfilter().filterFunction(function (d) {
                    for (i = 0; i < newValue.length; i++) {
                        if (d === newValue[i]) {
                            return true;
                        }
                    }
                 });
                }
                console.log('filters: ', scope.filters, 'length', hits.top(Infinity).length);
                scope.$parent.heatMapDataFilters[scope.filterType] = hits;
                console.log(scope.$parent.heatMapDataFilters);
                scope.$parent.setHeatMapData();
              });

            var pie = d3.layout.pie()
                .sort(null)
                .value(function(d) { return scope.data.length; });

            var arc = d3.svg.arc()
              .innerRadius(innerRadius)
              .outerRadius(function (d) {
                return (radius - innerRadius) * (d.data.value / (max + (max * .1))) + innerRadius;
              });

            var outlineArc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(radius);

            var svg = d3.select("#" + id + ' svg')
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

            var drag = d3.behavior.drag()
                .origin(function(d, i) { return d; })
                .on("dragstart", dragmove)
                .on("dragend", dragend);

            function dragmove(d) {
              dragging = true;
              d3.selectAll(this.parentElement.childNodes)
                  .filter('.aster-selected')
                  .classed('aster-selected', false);
              //d3.select(this).classed('aster-selected', true);
            }

            function dragend(d) {
                dragging = false;
                var hits = scope.crossfilter().filter(null);
            }
          scope.data.forEach(function(d) {
            d.order = 1;
            d.weight = 1;
            d.score = d.value;
            d.label =  d.key;
          });



          scope.selectObject = function(d) {
            if (dragging) {
                d3.select(this).classed("aster-selected", !d3.select(this).classed("aster-selected"));

                if (d3.select(this).classed("aster-selected")) {
                    console.log('about to update', scope.filters);
                    scope.filters.push(d.data.key);
                    scope.$apply();
                } else {
                    i = scope.filters.indexOf(d.data.key);
                    if (i > -1) {
                        scope.filters.splice(i, 1);
                    }
                }
            }
          };

          var outerPath = svg.selectAll(".outlineArc")
              .data(pie(scope.data))
            .enter().append("path")
              .attr("fill", "#efefef")
              .attr("opacity", ".6")
              .attr("stroke", "white")
              .attr("stroke-width", "2")
              .attr("class", "outlineArc")
              .attr("d", outlineArc)
              .on("click", handleClick)
              .call(drag)
              .on('mouseover', scope.selectObject);

          var path = svg.selectAll(".solidArc")
              .data(pie(scope.data))
            .enter().append("path")
              .attr("fill", "#ccc")
              .attr("class", "solidArc")
              .attr("stroke", "white")
              .attr("stroke-width", "1")
              .attr("d", arc)
              .on("click.handle", handleClick)
              .call(drag)
              .on('mouseover', scope.selectObject);

              svg.selectAll('.solidArcLabel')
                .data(pie(scope.data)).enter().append('text')
                .attr("dy", ".35em")
                  .attr("transform", function(d) {
                    var c = arc.centroid(d),
                        x = c[0],
                        y = c[1],
                        h = Math.sqrt(x*x + y*y);
                    return "translate(" + ((x/h * labelr)-3) +  ',' +
                       (y/h * labelr) +  ")";
                }).attr('class', 'aster-label')
                .text(function(d) { console.log(d); return d.data.key; });

          function query(element) {
            d3.selectAll(element.parentElement.childNodes)
                .filter('.aster-selected')
                .each(function(d) {
                    console.log('adding ' + d + 'to filter');
                })
          }

          function handleClick(d, i) {
              var selected = d3.selectAll(this.parentElement.childNodes).filter('.aster-selected');

              if (selected.empty()){
               d3.select(this).classed('aster-selected', true);
              } else if (selected[0].length == 1) {
                  if (selected[0].indexOf(this) > -1) {
                    d3.select(this).classed('aster-selected', false);
                  } else {
                    selected.classed('aster-selected', false);
                    d3.select(this).classed('aster-selected', true);
                  }
              } else if (selected[0].length > 1) {
                  d3.select(this).classed('aster-selected', true);
                  d3.selectAll(this.parentElement.childNodes)
                  .filter(function(n){console.log(n!==d);return n!==d})
                  .classed("aster-selected", false);
              }

              scope.filters = [];
              //console.log(query(this));
              scope.filters.push(d.data.key);
              scope.$apply();
          }
          // calculate the weighted mean score
          var score =
            scope.data.reduce(function(a, b) {
              return a + (b.value * b.weight);
            }, 0) /
            scope.data.reduce(function(a, b) {
              return a + b.weight;
            }, 0);

          }
        };
  });

  module.directive('bulletChart',
      function() {
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
              var chartElement =  '#' + id + ' svg';
              // ranges are the background
              // measures are the middle line
              // markers are the vertical line
              scope.data = [{"ranges":scope.ranges, "measures": scope.measures, "markers": scope.markers}];


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
      });
}());


