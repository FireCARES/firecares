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
             markers: '=',
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


