(function ($) {
    "use strict";

    jQuery(window).load(function () {
        if ($().isotope && ($('.ct-gallery').length > 0)) {

            var $container = $('.ct-gallery'), // object that will keep track of options
                isotopeOptions = {}, // defaults, used if not explicitly set in hash
                defaultOptions = {
                    filter: '*', itemSelector: '.ct-gallery-item', // set columnWidth to a percentage of container width
                    masonry: {
                    }
                };
            // set up Isotope
            $container.isotope(defaultOptions);

            $container.imagesLoaded().progress(function (instance, image) {
                if (!image.isLoaded) {
                    return;
                }

                var p = $(image.img).closest('.hidden');
                p.removeClass('hidden');
                $container.addClass('is-loaded')

                $container.isotope('layout');
            })

            $('.ct-gallery-filters a').click(function () {
                $('.ct-gallery-filters .active').removeClass('active');
                $(this).addClass('active');

                var selector = $(this).attr('data-filter');
                $container.isotope({
                    filter: selector, animationOptions: {
                        duration: 750, easing: 'linear', queue: false
                    }
                });
                return false;
            });
        }
    });
}(jQuery));