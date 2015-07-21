(function ($) {
    "use strict";

    $(document).ready(function () {

        // Progress Bars // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        if (($().appear) && ($("body").hasClass("cssAnimate"))) {
            $('.progress').appear(function () {
                var $this = $(this);
                $this.each(function () {
                    var $innerbar = $this.find(".progress-bar");
                    var percentage = $innerbar.attr("aria-valuenow");
                    $innerbar.addClass("animating").css("width", percentage + "%");

                });
            }, {accY: -100});
        } else {
            $('.progress').each(function () {
                var $this = $(this);
                var $innerbar = $this.find(".progress-bar");
                var percentage = $innerbar.attr("aria-valuenow");
                $innerbar.addClass("animating").css("width", percentage + "%");

            });
        }
    })
}(jQuery));