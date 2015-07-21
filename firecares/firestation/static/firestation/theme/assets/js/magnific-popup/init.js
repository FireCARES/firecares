(function ($) {
    "use strict";
    $(document).ready(function(){
        if(jQuery().magnificPopup){
            jQuery('.ct-js-magnificPortfolioPopupGroup').each(function() { // the containers for all your galleries
                jQuery(this).magnificPopup({
                    type: 'ajax',
                    delegate: '.ct-js-magnificPortfolioPopup',
                    mainClass: 'ct-magnificPopup-bottomArrows',
                    fixedContentPos: true,
                    closeBtnInside: true,
                    closeOnContentClick: false,
                    closeOnBgClick: false,
                    gallery: {
                        enabled: true
                    },
                    callbacks: {
                        ajaxContentAdded: function() {
                            $('.ct-js-flexsliderPopup').flexslider({
                                animationLoop: true,
                                animation: 'slide',
                                controlNav: false,
                                prevText: "",
                                nextText: ""
                            });
                        },
                        buildControls: function() {
                            // re-appends controls inside the main container
                            this.contentContainer.append(this.arrowLeft.add(this.arrowRight));
                        }

                    }
                });
            });

            $('.ct-js-magnificPopupMedia').magnificPopup({
                //disableOn: 700,
                type: 'iframe',
                mainClass: 'mfp-fade',
                removalDelay: 160,
                preloader: true,

                fixedContentPos: false
            });
            $('.ct-js-magnificPopupImage').magnificPopup({
                //disableOn: 700,
                type: 'image',
                mainClass: 'ct-magnificPopup--image',
                removalDelay: 160,
                preloader: true,

                fixedContentPos: false
            });
        }
    })
}(jQuery));