(function ($) {
    "use strict";
    $(document).ready(function () {
        if ($().pageScroller) {

            if($devicewidth < 768){
                $('body').pageScroller({
                    navigation: '.ct-menuMobile .onepage', sectionClass: 'section', scrollOffset: -70
                });
            } else{
                $('body').pageScroller({
                    navigation: '.nav.navbar-nav .onepage', sectionClass: 'section', scrollOffset: -70
                });
            }
        }
    })
})(jQuery);