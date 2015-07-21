(function ($) {
    "use strict";
    $(window).load(function () {
        /* ==================== */
        /* ==== PIE CHARTS ==== */
        $('.ct-js-pieChart').each(function () {
            var $this = $(this);
            var $color = validatedata($(this).attr('data-ct-firstColor'), "#2b8be9");
            var $color2 = validatedata($(this).attr('data-ct-secondColor'), "#eeeeee");
            var $cutout = validatedata($(this).attr('data-ct-middleSpace'), 90);
            var $stroke = validatedata($(this).attr('data-ct-showStroke'), false);
            var $margin = validatedata($(this).attr('data-ct-margin'), false);
            $(this).parent().css('margin-left',$margin + 'px');
            $(this).parent().css('margin-right',$margin + 'px');
            var options = {
                responsive: true, percentageInnerCutout: $cutout, segmentShowStroke: $stroke, showTooltips: false
            }
            var doughnutData = [{
                value: parseInt($this.attr('data-ct-percentage'), 10), color: $color, label: false
            }, {
                value: parseInt(100 - $this.attr('data-ct-percentage'), 10), color: $color2
            }];

            if (($().appear) && ($("body").hasClass("cssAnimate"))) {
                $('.ct-js-pieChart').appear(function () {
                    var ctx = $this[0].getContext("2d");
                    window.myDoughnut = new Chart(ctx).Doughnut(doughnutData, options);
                });
            } else {
                var ctx = $this[0].getContext("2d");
                window.myDoughnut = new Chart(ctx).Doughnut(doughnutData, options);
            }
        })

        var graph2options = {
            responsive: true,
            percentageInnerCutout : 0,
            showTooltips: true
        }
        var graph3options = {
            responsive: true,
            percentageInnerCutout : 0,
            showTooltips: false
        }
        var graph2doughnutData = [
            {
                value: 15,
                color: '#bf5252',
                label: "Red"
            },
            {
                value: 35,
                color: '#a2bf52',
                label: "Green"
            },
            {
                value: 50,
                color: '#60a7d4',
                label: "Blue"
            }
        ];
        var graph3doughnutData = [
            {
                value: 13,
                color: '#bf5252',
                label: "Red"
            },
            {
                value: 12,
                color: '#eb8a21',
                label: "Orange"
            },
            {
                value: 25,
                color: '#a2bf52',
                label: "Green"
            },
            {
                value: 50,
                color: '#60a7d4',
                label: "Blue"
            }
        ];
        if(jQuery().appear && jQuery("body").hasClass("withAnimation")) {
            jQuery('#graph2').appear(function () {
                var ctx = $(this)[0].getContext("2d");
                window.myDoughnut = new Chart(ctx).Doughnut(graph2doughnutData, graph2options);
            });
            jQuery('#graph3').appear(function () {
                var ctx = $(this)[0].getContext("2d");
                window.myDoughnut = new Chart(ctx).Doughnut(graph3doughnutData, graph3options);
            });
        } else{
            var ctx = document.getElementById("graph2").getContext("2d");
            window.myDoughnut = new Chart(ctx).Doughnut(graph2doughnutData, graph2options);
            var ctx = document.getElementById("graph3").getContext("2d");
            window.myDoughnut = new Chart(ctx).Doughnut(graph3doughnutData, graph3options);
        }
    })
})(jQuery);