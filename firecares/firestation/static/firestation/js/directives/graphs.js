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
}());


