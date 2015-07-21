function makekenburns($element) {
    // we set the 'fx' class on the first image
    // when the page loads
    $element.find('img')[0].className = "fx";

    // the third variable is to keep track of
    // where we are in the loop
    // if it is set to *1* (instead of 0)
    // it is because the first image is styled
    // when the page loads
    var images = $element.find('img'), numberOfImages = images.length, i = 1;
    if (numberOfImages == 1) {
        images[0].className = "singlefx";
    }
    // this calls the kenBurns function every
    // 4 seconds. You can increase or decrease
    // this value to get different effects
    window.setInterval(kenBurns, 7000);

    function kenBurns() {
        if (numberOfImages != 1) {
            if (i == numberOfImages) {
                i = 0;
            }
            images[i].className = "fx";
            // we can't remove the class from the previous
            // element or we'd get a bouncing effect so we
            // clean up the one before last
            // (there must be a smarter way to do this though)
            if (i === 0) {
                images[numberOfImages - 2].className = "";
            }
            if (i === 1) {
                images[numberOfImages - 1].className = "";
            }
            if (i > 1) {
                images[i - 2].className = "";
            }
            i++;
        }
    }
}

(function ($) {
    "use strict";

    $(document).ready(function () {

        // Page Section PARALLAX // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        if ($().stellar && !device.isIE8) {
            if (!device.mobile() && !device.ipad() && !device.androidTablet()) {
                $(window).stellar({
                    horizontalScrolling: false, responsive: true, positionProperty: 'transform'
                });
            }
        }

        // Page Section DEFAULTS // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        $(".ct-mediaSection").each(function () {
            var $this = $(this);
            var $height = $this.attr("data-height");

            // Page Section HEIGHT // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if(!(typeof $height === 'undefined')){
                if ($height.indexOf("%") > -1) {
                    $this.css('min-height', $deviceheight);
                    $this.css('height', $deviceheight);
                    if(!device.mobile()){
                        $this.css('height', $deviceheight + "px");
                        $this.css('min-height', $deviceheight + "px");
                    }
                } else {
                    $this.css('min-height', $height + "px");
                    $this.css('height', $height + "px");
                    if(jQuery.browser.mozilla){
                        $this.css('height', $height + "px");
                        $this.css('min-height', $height + "px");
                    }
                }
            }

            // Page Section BACKGROUND COLOR // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if($this.attr('data-type')=="color"){
                var $bg_color = $this.attr("data-bg-color");
                $this.css('background-color', $bg_color);
            }

            // Page Section BACKGROUND IMAGE // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

            if($this.attr('data-type')=="pattern" || $this.attr('data-type')=="parallax" || $this.attr('data-type')=="video" || $this.attr('data-type')=="kenburns"){
                var $bg_image_fallback = $this.attr("data-bg-image-mobile");
                if (!(device.mobile() || device.ipad() || device.androidTablet())){
                    if($this.attr('data-type')=="pattern" || $this.attr('data-type')=="parallax") {
                        var $bg_image = $this.attr("data-bg-image");
                        $this.css('background-image', 'url("' + $bg_image + '")');
                    }
                } else{
                    $this.css('background-image', 'url("' + $bg_image_fallback + '")');
                }

                // Page Section BACKGROUND POSITION FOR iDevices // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

                if (device.mobile() || device.ipad() || device.androidTablet() || device.isIE8) {
                    $this.css('background-attachment', 'scroll'); // iOS SUCKS
                }
            }

            // Page Section KENBURNS // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

            if($this.attr('data-type')=="kenburns"){
                var images = $this.find('.ct-mediaSection-kenburnsImageContainer img');

                if (!(device.mobile() || device.ipad() || device.androidTablet())) {
                    makekenburns($this.find('.ct-mediaSection-kenburnsImageContainer'));
                } else {
                    images.each(function () {
                        $(this).remove();
                    })
                }
            }

            // Page Section VIDEO // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

            if($this.attr('data-type')=="video"){
                var $this = $(this);
                var $height = $this.attr("data-height");
                var $time = 1;

                if ($height.indexOf("%") > -1) {
                    $this.css('min-height', $deviceheight);
                    $this.find('> .ct-u-displayTable').css('height', $deviceheight);
                } else {
                    $this.css('min-height', $height + "px");
                    $this.find('> .ct-u-displayTable').css('height', $height + "px");
                }
                if (!$this.hasClass("html5")) {
                    var $videoframe = $this.find('iframe')
                    if ($videoframe.attr('data-startat')) {
                        $time = $videoframe.attr('data-startat');
                    }
                    if (!($devicewidth < 992) && !device.mobile()) {
                        if (typeof $f != 'undefined') {
                            var $video = '#' + $videoframe.attr('id');
                            var iframe = $($video)[0], player = $f(iframe), status = $('.status');


                            player.addEvent('ready', function () {
                                player.api('setVolume', 0);
                                player.api('seekTo', $time);
                            })
                        }
                    }
                } else {
                    //THIS IS WHERE YOU CALL THE VIDEO ID AND AUTO PLAY IT. CHROME HAS SOME KIND OF ISSUE AUTOPLAYING HTML5 VIDEOS, SO THIS IS NEEDED
                    document.getElementById('video1').play();
                }
                if ($devicewidth < 992 || device.mobile() || device.ipad() || device.androidTablet()) {
                    $this.find(".ct-mediaSection-video").css('display', 'none');
                }
            }

        })

        // Page Section PARALLAX // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        $(".stellar-object").each(function () {
            var $this = $(this);
            var $bg = $this.attr("data-image");
            var $height = $this.attr("data-height") + 'px';
            var $width = $this.attr("data-width") + 'px';
            var $top = $this.attr("data-top");
            var $left = $this.attr("data-left");

            $this.css('background-image', 'url("' + $bg + '")');
            $this.css('width', $width);
            $this.css('height', $height);
            $this.css('top', $top);
            $this.css('left', $left);
        })

    })
})(jQuery);