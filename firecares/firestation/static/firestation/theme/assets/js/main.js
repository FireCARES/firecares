/**
 * createIT main javascript file.
 */

var $lgWidth = 1199;
var $mdWidth = 991;
var $smWidth = 767;
var $xsWidth = 479;

var $devicewidth = (window.innerWidth > 0) ? window.innerWidth : screen.width;
var $deviceheight = (window.innerHeight > 0) ? window.innerHeight : screen.height;
var $bodyel = jQuery("body");
var $navbarel = jQuery(".navbar");
var $topbarel = jQuery(".ct-topBar");

/* ========================== */
/* ==== HELPER FUNCTIONS ==== */

function validatedata($attr, $defaultValue) {
    "use strict";
    if ($attr !== undefined) {
        return $attr
    }
    return $defaultValue;
}

function parseBoolean(str, $defaultValue) {
    "use strict";
    if (str == 'true') {
        return true;
    } else if (str == "false") {
        return false;
    }
    return $defaultValue;
}

// Kenburns //-----------------------------

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

    // Init Snap //-------------------------------

    if(document.getElementById('ct-js-wrapper')){
        var snapper = new Snap({
            element: document.getElementById('ct-js-wrapper')
        });

        snapper.settings({
            addBodyClasses: true,
            slideIntent: 20
        });
    }

    $(window).load(function(){

        $('.owl-carousel .owl-item').css('opacity', '1')
        $('.owl-carousel .owl-item img').css('opacity', '1')

        // Section Color // -------------------------------------------

        $(".ct-js-section").each(function () {
            var $this = $(this);
            $this.css('background-color', $this.attr("data-bg-color"));
        })

        // Animations Init // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        if ($().appear) {
            if (device.mobile() || device.tablet()) {
                $("body").removeClass("cssAnimate");
            } else {

                $('.cssAnimate .animated').appear(function () {
                    var $this = $(this);

                    $this.each(function () {
                        if ($this.data('time') != undefined) {
                            setTimeout(function () {
                                $this.addClass('activate');
                                $this.addClass($this.data('fx'));
                            }, $this.data('time'));
                        } else {
                            $this.addClass('activate');
                            $this.addClass($this.data('fx'));
                        }
                    });
                }, {accX: 50, accY: -350});
            }
        }

        // Parallax Disable // ------------------------------------------

        if (($(window).width()<=1024)) {
            $(".ct-mediaSection").removeAttr("data-stellar-background-ratio").removeAttr("data-type").addClass("ct-u-backgroundfix");
        }
    });

    $(document).ready(function () {

        // Add Color // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        $(".ct-js-color").each(function(){
            $(this).css("color", '#' + $(this).attr("data-color"))
        })

        var select2 = $('.ct-js-select');

        if(select2.length > 0){
            select2.select2();
        }

        // Media Sections // ------------------------------------------------

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

        // Snapper Disable //--------------------------------------------

        if ($devicewidth > 767 && document.getElementById('ct-js-wrapper')) {
            snapper.disable();
        }
        $(".ct-js-owl").attr("data-snap-ignore", true)

        // Snap Navigation in Mobile // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        $(".navbar-toggle").on("click", function () {
            if($bodyel.hasClass('snapjs-left')){
                snapper.close();
            } else{
                snapper.open('left');
            }
        });

        $(".searchForm-toggle").on("click", function () {
            if($bodyel.hasClass('snapjs-right')){
                snapper.close();
            } else{
                snapper.open('right');
            }
        });

        $('.ct-menuMobile .ct-menuMobile-navbar .onepage > a').on("click", function(e) {
            snapper.close();
        })

        //Animation Maintenance page

        if ($devicewidth<=767) {
            $(".ct-animation--container div").removeClass("rotating rotating--reverse ")
        }

        //Open mobile menu

        $('.ct-menuMobile-navbar li.dropdown').on("click", function () {
            $( this ).has( "ul" ).toggleClass("ct-js-dropdown-mobile").siblings().removeClass('ct-js-dropdown-mobile');
        });

        $('.ct-menuMobile-navbar li.dropdown-submenu').on("click", function () {
            $( this ).has( "ul" ).toggleClass("ct-js-dropdown-mobile").siblings().removeClass('ct-js-dropdown-mobile');
        });

        //Hide navigation in mobile(gmaps)

        if($('.ct-googleMap').hasClass('ct-js-googleMap--single')){
            $('.ct-navigationGmaps').addClass('hidden');
        }

        //Bootstrap slider init
        if($('.slider').length > 0){
            $('.slider').slider();
        }


        // Range Slider // ----------------------------------------------------------------
        var $sliderAmount = $('.ct-sliderAmount'); // TODO
        jQuery.each($sliderAmount, function(){
            var $this = $(this);

            var $slidermin = $this.find('.ct-js-slider-min');
            var $slidermax = $this.find('.ct-js-slider-max');
            var $sliderrange = $this.find('.ct-js-sliderAmount');

            $sliderrange.on('slide', function(){
                var newvalue = $sliderrange.data('slider').getValue();

                $slidermin.val(newvalue[0]);  //Add value on inputs
                $slidermax.val(newvalue[1]);

            });
        });

        // Navbar Search // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        var $searchform = $(".ct-navbar-search");
        $('#ct-js-navSearch').on("click", function(e){
            e.preventDefault();
            $navbarel.addClass('is-inactive');


            $searchform.fadeIn();

            if (($searchform).is(":visible")) {
                $searchform.find("[type=text]").focus();
            }

            return false;
        })

        // Placeholder Fallback // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        if ($().placeholder) {
            $("input[placeholder],textarea[placeholder]").placeholder();
        }

        /*
         ****************
         shopList and shopDefault displaying and hiding elements by buttons
         ****************
         */

        var $tilesItems = $("#ct-js-showTiles");
        var $listItems = $("#ct-js-showList");
        var $showProducts = $(".ct-js-search-results");

        if($tilesItems && $listItems){
            $tilesItems.on("click", function(e){
                e.preventDefault();

                if(!$tilesItems.hasClass("is-active"))
                {
                    var $existListClass = $(".ct-showProducts--list");

                    if($existListClass){
                        $showProducts.removeClass("ct-showProducts--list");
                        $showProducts.addClass("ct-showProducts--default");
                        $showProducts.css("display", "none");
                        $showProducts.fadeIn();

                        $(this).addClass("is-active");
                        $listItems.removeClass("is-active");
                    }
                }
            });

            $listItems.on("click", function(e){
                e.preventDefault();

                if(!$listItems.hasClass("is-active")){
                    var $existDefaultClass = $(".ct-showProducts--list");

                    if($existDefaultClass){
                        $showProducts.removeClass("ct-showProducts--default");
                        $showProducts.addClass("ct-showProducts--list");
                        $showProducts.css("display", "none");
                        $showProducts.fadeIn();

                        $(this).addClass("is-active");
                        $tilesItems.removeClass("is-active");
                    }
                }
            });
        }

        // Tabs Cycle () ------ .ct-testimonials .row ul > li -----------------------------------------------------------------------------------------------------------------------

        var tabChange = function(){
            var tabs = $('.ct-testimonials > .row > ul > li');
            var active = tabs.filter('.active');
            var next = active.next('li').length ? active.next('li').find('a') : tabs.filter(':first-child').find('a');
            next.tab('show');
        };
        var tabCycle = setInterval(tabChange, 5000);
        //--------------------------------------------------------------------------------------
        $('.ct-testimonials > .row > ul > li > a').on('click', function (e) {
            e.preventDefault();
            // Stop the cycle
            clearInterval(tabCycle);
            // Show the clicked tabs associated tab-pane
            $(this).tab('show');
            // Start the cycle again in a predefined amount of time
            tabCycle = setInterval(tabChange, 5000);
            return false;
        });

        // Footer button to top // --------------------------

        $('.ct-js-btnScrollUp').on("click", function () {
            $("body,html").animate({scrollTop: 0}, 1200);
            return false;
        });

        // Button Scroll to Section // -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        $('.ct-js-btnScroll[href^="#"]').on("click", function (e) {
            e.preventDefault();

            var target = this.hash, $target = $(target);

            $('html, body').stop().animate({
                'scrollTop': -100+$target.offset().top
            }, 900, 'swing', function () {
                window.location.hash = target;
            });
        });

        // Datepicker init // --------------------------------

        if($('.ct-widget-categories').hasClass('ct-js-datetimePicker')){
            $('.ct-js-datetimePicker .ct-js-datetimePicker--body').datepicker({
                todayHighlight: true
            });
        }


        //Tooltip // -----------------------------------------

        $("[data-toggle='tooltip']").tooltip();

        $("[data-toggle='popover']").popover({trigger: "hover", html: true});

        //Popup form center // --------------------------------

        function centerForm(form){
            var $wrapperOuterHeight = form.height();
            var $wrapperOuterWidth = form.width();
            if($deviceheight <= 480){
                var left = 0;
                //var top = 0 ;
            }
            else{
                var left = ($devicewidth / 2) - ($wrapperOuterWidth / 2);
                //var top = ($deviceheight / 2) - ($wrapperOuterHeight / 2) ;
            }
            form.css({
                "position": "absolute",
                "left": left  + "px",
                "top": 100  + "px"
            });
        }

        //Popup form // --------------------------------------

        var $popupForm = $(".ct-popupForm");
        var $popupMain = $(".ct-js-productForm--main");
        var $popupMap = $(".ct-js-productForm--map");
        var $popupDetails = $(".ct-js-productForm--details");
        var $popupAgents = $(".ct-js-productForm--agents");
        var $popupProperties = $(".ct-js-productForm--properties");

        var $popupmask = $(".mask");
        var $popupclose = $(".ct-form-close");

        var $btnEditMain = $(".ct-js-btnEdit--Main");
        var $btnEditMap = $(".ct-js-btnEdit--Map");
        var $btnEditDetails = $(".ct-js-btnEdit--Details");
        var $btnEditAgents = $(".ct-js-btnEdit--Agents");
        var $btnEditProperties = $(".ct-js-btnEdit--Properties");

        $btnEditMain.on("click", function(){
            $popupMain.removeClass("infinite-left");
            $popupmask.removeClass("infinite-left");
            centerForm($popupMain);
        });
        $btnEditMap.on("click", function(){
            $popupMap.removeClass("infinite-left");
            $popupmask.removeClass("infinite-left");
            centerForm($popupMap);
        });
        $btnEditDetails.on("click", function(){
            $popupDetails.removeClass("infinite-left");
            $popupmask.removeClass("infinite-left");
            centerForm($popupDetails);
        });
        $btnEditAgents.on("click", function(){
            $popupAgents.removeClass("infinite-left");
            $popupmask.removeClass("infinite-left");
            centerForm($popupAgents);
        });
        $btnEditProperties.on("click", function(){
            $popupProperties.removeClass("infinite-left");
            $popupmask.removeClass("infinite-left");
            centerForm($popupProperties);
        });
        $popupmask.on("click", function(){
            $popupForm.addClass("infinite-left");
            $popupmask.addClass("infinite-left");
        });
        $popupclose.on("click", function(){
            $popupForm.addClass("infinite-left");
            $popupmask.addClass("infinite-left");
        });

// ============================= Headroom ============================================

        var $headroomStr = "ct-js-headroom";
        var $headroomCla = ".ct-js-headroom";
        var $topBarStr = "ct-topBar";
        var $navBarStr = "navbar";

        if($bodyel.hasClass("ct-headroom--scrollUpMenu")){
            $navbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--scrollUpTopBar")){
            $topbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--scrollUpBoth")){
            var $scrollUpBoth = true;
            $topbarel.addClass($headroomStr);
            $navbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--fixedTopBar")){
            var $fixedTopBar = true;
            $topbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--fixedMenu")){
            var $fixedMenu = true;
            $navbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--fixedBoth")){
            var $fixedBoth = true;
            var $scrollUpBoth = true;
            $topbarel.addClass($headroomStr);
            $navbarel.addClass($headroomStr);
        }
        else if($bodyel.hasClass("ct-headroom--hideMenu")){
            var $fixedScrollUpTopBar = true;
            var $scrollUpTopBar = true;
            $topbarel.addClass($headroomStr);
            $navbarel.addClass($headroomStr);
        }
        else{
            return;
        }

        if($($headroomCla).length > 0){
            $($headroomCla).each(function(){
                var $this = $(this);

                //Position of the topBar and navbar, when (scroll position) we grab it
                var $startPositionTopBar = 0;
                var $startPositionNavbar = 118;

                var ctstarttopbar = validatedata($this.attr("data-starttopbar"), $startPositionTopBar); //default position 0
                var ctstartnavbar = validatedata($this.attr("data-startnavbar"), $startPositionNavbar); //default position 170

                $(window).scroll(function(){
                    var scrollPos = $(window).scrollTop();

                    if ($this.hasClass($topBarStr)){
                        if (scrollPos > ctstarttopbar){
                            $this.addClass("navbar-scroll-top");
                        }
                        else{
                            $this.removeClass("navbar-scroll-top");
                        }
                    }
                    else if($this.hasClass($navBarStr)){
                        if (scrollPos >  ctstartnavbar){
                            $this.addClass("navbar-scroll-top");

                            if($scrollUpBoth || $scrollUpTopBar){
                                //this attribute we put in navbar only if we use ct-headroom--scrollUpBoth, ct-headroom--fixedBoth, ct-headroom--hideMenu
                                var ctheighttopbar = validatedata($this.attr("data-heighttopbar"), "50px"); // height of topbar needed for positiong menu below topbar exact how height is topbar :)
                                $this.css("top",ctheighttopbar); //add 50px for menu coz topbar has 50px, we want to put it below
                            }
                        }
                        else{
                            $this.removeClass("navbar-scroll-top");
                            if($scrollUpBoth || $scrollUpTopBar){
                                $this.css("top","auto");
                            }
                        }
                    }
                });

                var ctoffset = validatedata($this.attr("data-offset"), 205); //this is the offset when taken elements have to disappear

                var cttolerance = validatedata($this.attr("data-tolerance"), 5); /// you can specify tolerance individually for up/down scroll
                var ctinitiial = validatedata($this.attr("data-initial"), "animatedHeadroom"); // when element is initialised
                var cttop = validatedata($this.attr("data-top"), "headroom--top");  // when above offset
                var ctnotTop = validatedata($this.attr("data-top"), "headroom--not-top"); // when below offset

                if($fixedScrollUpTopBar){
                    if($this.hasClass("ct-topBar")){
                        var $fixedScrollUpTopBarConfirmed = true;
                    }
                }

                if($fixedBoth || $fixedTopBar || $fixedMenu || $fixedScrollUpTopBarConfirmed){
                    //if you want to fix elements for good, then we should change variables so that they are with the same name, no matter what
                    var ctpinned = validatedata($this.attr("data-pinned"), "IAmFixed");
                    var ctunpinned = validatedata($this.attr("data-unpinned"), "IAmFixed");
                }
                else{
                    var ctpinned = validatedata($this.attr("data-pinned"), "fadeInDown"); //effect when elements appears itself -  when scrolling up
                    var ctunpinned = validatedata($this.attr("data-unpinned"), "fadeOutUp"); //effect when elements disappears itself -  when scrolling down
                }

                $this.headroom({ //do this for each element use  add .ct-js-headroom

                    "offset": ctoffset,// vertical offset in px before element is first unpinned
                    "tolerance": cttolerance, // scroll tolerance in px before state changes
                    "top": cttop, // when above offset
                    "notTop": ctnotTop, // when below offset

                    "classes": {
                        "initial": ctinitiial, // when element is initialised
                        "pinned": ctpinned, // when scrolling up
                        "unpinned": ctunpinned // when scrolling down
                    }
                });
            });
        }

        // OWL CORUSEL // -------------------------------

        if($().owlCarousel){
            if ($(".ct-js-owl").length > 0) {
                $(".ct-js-owl").each(function (){
                    var $this = $(this);

                    var ctanimations = validatedata($this.attr("data-animations"), false);

                    if($devicewidth < 768 || device.mobile() || device.ipad() || device.androidTablet()){
                        ctanimations = false;
                    }

                    var ctitems = parseInt(validatedata($this.attr("data-items"), 5), 10);
                    var $lgItems = parseInt(validatedata($this.attr("data-lgItems"), 4), 10);
                    var $mdItems = parseInt(validatedata($this.attr("data-mdItems"), 3), 10);
                    var $smItems = parseInt(validatedata($this.attr("data-smItems"), 2), 10);
                    var $xsItems = parseInt(validatedata($this.attr("data-xsItems"), 1), 10);
                    var ctsingleitem = parseBoolean($this.attr("data-single"), true);
                    var ctscaleitems = parseBoolean($this.attr("data-scaleUp"), false);

                    var ctslidespeed = parseInt(validatedata($this.attr("data-slideSpeed"), 200), 10);
                    var ctpagspeed = parseInt(validatedata($this.attr("data-paginationSpeed"), 800), 10);
                    var ctrewindspeed = parseInt(validatedata($this.attr("data-rewindSpeed"), 1000), 10);

                    var ctautoplay = parseBoolean($this.attr("data-autoPlay"), false);
                    if($this.attr("data-autoPlaySpeed") != null){
                        ctautoplay = parseInt(validatedata($this.attr("data-autoPlaySpeed"), 5000), 10);
                    }
                    var ctstophover = parseBoolean($this.attr("data-stopOnHover"), false);

                    var ctnavigation = parseBoolean($this.attr("data-navigation"), true);
                    var ctrewindnav = parseBoolean($this.attr("data-rewindNav"), true);
                    var ctscrollperpage = parseBoolean($this.attr("data-scrollPerPage"), false)

                    var ctpagination = parseBoolean($this.attr("data-pagination"), true);
                    var ctpaginationnumbers = parseBoolean($this.attr("data-paginationNumbers"), false);

                    var ctresponsive = parseBoolean($this.attr("data-responsive"), true);

                    var ctlazyload = parseBoolean($this.attr("data-lazyLoad"), false);

                    var ctautoheight = parseBoolean($this.attr("data-autoHeight"), false);

                    var ctmouse = parseBoolean($this.attr("data-mouse"), true);
                    var cttouch = parseBoolean($this.attr("data-touch"), true);

                    var cttransition = validatedata($this.attr("data-cttransition"), "fade");

                    $this.owlCarousel({
                        // Most important owl features
                        items : ctitems, //This variable allows you to set the maximum amount of items displayed at a time with the widest browser width
                        itemsDesktop : [$lgWidth,$lgItems], //This allows you to preset the number of slides visible with a particular browser width. The format is [x,y] whereby x=browser width and y=number of slides displayed. For example [1199,4] means that if(window<=1199){ show 4 slides per page} Alternatively use itemsDesktop: false to override these settings.
                        itemsDesktopSmall : [$mdWidth,$mdItems], //As above.
                        itemsTablet: [$smWidth,$smItems], // As above.
                        itemsMobile : [$xsWidth,$xsItems], // As above.
                        singleItem : ctsingleitem, // Display only one item.
                        itemsScaleUp : ctscaleitems, // Option to not stretch items when it is less than the supplied items.

                        //Basic Speeds
                        slideSpeed : ctslidespeed, // Slide speed in milliseconds
                        paginationSpeed : ctpagspeed, // Pagination speed in milliseconds
                        rewindSpeed : ctrewindspeed, // Rewind speed in milliseconds

                        //Autoplay
                        autoPlay : ctautoplay, // Change to any integrer for example autoPlay : 5000 to play every 5 seconds. If you set autoPlay: true default speed will be 5 seconds.
                        stopOnHover : ctstophover, // Stop autoplay on mouse hover

                        // Navigation
                        navigation : ctnavigation, // Display "next" and "prev" buttons.
                        navigationText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'], // You can customize your own text for navigation. To get empty buttons use navigationText : false. Also HTML can be used here
                        rewindNav : ctrewindnav, // Slide to first item. Use rewindSpeed to change animation speed.
                        scrollPerPage : ctscrollperpage, // Scroll per page not per item. This affect next/prev buttons and mouse/touch dragging.

                        //Pagination
                        pagination : ctpagination, // Show pagination.
                        paginationNumbers: ctpaginationnumbers, // Show numbers inside pagination buttons

                        // Responsive
                        responsive: ctresponsive, // You can use Owl Carousel on desktop-only websites too! Just change that to "false" to disable resposive capabilities
                        responsiveRefreshRate : 200, // Check window width changes every 200ms for responsive actions
                        responsiveBaseWidth: window, // Owl Carousel check window for browser width changes. You can use any other jQuery element to check width changes for example ".owl-demo". Owl will change only if ".owl-demo" get new width.

                        // CSS Styles
                        baseClass : "owl-carousel", // Automaticly added class for base CSS styles. Best not to change it if you don't need to.
                        theme : "owl-theme", // Default Owl CSS styles for navigation and buttons. Change it to match your own theme

                        //Lazy load
                        lazyLoad : ctlazyload, // Delays loading of images. Images outside of viewport won't be loaded before user scrolls to them. Great for mobile devices to speed up page loadings. IMG need special markup class="lazyOwl" and data-src="your img path". See example.
                        lazyFollow : true, // When pagination used, it skips loading the images from pages that got skipped. It only loads the images that get displayed in viewport. If set to false, all images get loaded when pagination used. It is a sub setting of the lazy load function.
                        lazyEffect : "fade", // Default is fadeIn on 400ms speed. Use false to remove that effect.

                        //Auto height
                        autoHeight : ctautoheight,

                        //JSON
                        jsonPath : false,
                        jsonSuccess : false,

                        //Mouse Events
                        dragBeforeAnimFinish : true,
                        mouseDrag : ctmouse,
                        touchDrag : cttouch,

                        //Transitions
                        transitionStyle : cttransition, // Add CSS3 transition style. Works only with one item on screen.

                        // Other
                        addClassActive : true, // Add "active" classes on visible items. Works with any numbers of items on screen.

                        //Callbacks
                        beforeUpdate : false,
                        afterUpdate : false,
                        beforeInit: function () {

                        },
                        afterInit: function(){

                            if(ctanimations) {
                                $this.css('min-height', $this.attr('data-height'));
                                $this.css('height', $this.attr('data-height'));
                                $this.find('.owl-wrapper-outer').css('min-height', $this.attr('data-height'));
                                $this.find('.owl-wrapper-outer').css('height', $this.attr('data-height'));
                                $this.find('.owl-wrapper').css('min-height', $this.attr('data-height'));
                                $this.find('.owl-wrapper').css('height', $this.attr('data-height'));
                                $this.find(".item").each(function () {
                                    var $slide_item = $(this);
                                    var bg = validatedata($slide_item.attr('data-bg'), false);
                                    if (bg) {
                                        $slide_item.css('background-image', 'url("' + bg + '")');
                                    }
                                })

                                setTimeout(function () {
                                    $this.find(".owl-item.active > .item [data-fx]").each(function () {
                                        var $content = $(this);
                                        if ($content.data('time') != undefined) {
                                            setTimeout(function () {
                                                $content.addClass($content.data('fx')).addClass("activate");
                                            }, $content.data('time'));
                                        } else{
                                            $content.addClass($content.data('fx')).addClass("activate");
                                        }
                                    })
                                }, 650);
                            }
                        },
                        beforeMove: false,
                        afterMove: false,
                        afterAction:  function(){
                            if(ctanimations){
                                $this.find(".owl-item > .item [data-fx]").each(function () {
                                    var $content = $(this);
                                    $content.removeClass($content.data('fx')).removeClass("activate");
                                })
                                setTimeout(function () {
                                    $this.find(".owl-item.active > .item [data-fx]").each(function () {
                                        var $content = $(this);
                                        if ($content.data('time') != undefined) {
                                            setTimeout(function () {
                                                $content.addClass($content.data('fx')).addClass("activate");
                                            }, $content.data('time'));
                                        } else{
                                            $content.addClass($content.data('fx')).addClass("activate");
                                        }
                                    })
                                }, 150);
                            }
                        },
                        startDragging : false,
                        afterLazyLoad : false
                    })
                })
            }
        }
        var sync1 = $("#sync1");
        var sync2 = $("#sync2");

        if($(".ct-owl--background").hasClass("ct-mediaSection")){
            //Fix for autoplay video in owl
            $(this).find('video').get(0).play();
        }

        function syncPosition(el){
            var current = this.currentItem;
            sync2
                .find(".owl-item")
                .removeClass("synced")
                .eq(current)
                .addClass("synced")
            if(sync2.data("owlCarousel") !== undefined){
                center(current)
            }
        }

        //function syncPosition2(el){
        //    var current2 = this.currentItem;
        //    sync1
        //        .find(".owl-item")
        //        .removeClass("syncedMain")
        //        .eq(current2)
        //        .addClass("syncedMain")
        //    if(sync1.data("owlCarousel") !== undefined){
        //        center2(current2)
        //    }
        //}

        function center(number){
            var sync2visible = sync2.data("owlCarousel").owl.visibleItems;
            console.log(sync2visible);
            var num = number;
            var found = false;
            for(var i in sync2visible){
                if(num === sync2visible[i]){
                    found = true;
                }
            }

            if(found===false){
                if(num>sync2visible[sync2visible.length-1]){
                    sync2.trigger("owl.goTo", num - sync2visible.length+2)
                }else{
                    if(num - 1 === -1){
                        num = 0;
                    }
                    sync2.trigger("owl.goTo", num);
                }
            } else if(num === sync2visible[sync2visible.length-1]){
                sync2.trigger("owl.goTo", sync2visible[1])
            } else if(num === sync2visible[0]){
                sync2.trigger("owl.goTo", num-1)
            }

        }

        //function center2(number){
        //    var sync1visible = sync1.data("owlCarousel").owl.visibleItems;
        //    console.log(sync1visible);
        //    var num2 = number;
        //    var found2 = false;
        //    for(var i in sync1visible){
        //        if(num2 === sync1visible[i]){
        //            found2 = true;
        //        }
        //    }
        //
        //    if(found2===false){
        //        if(num2>sync1visible[sync1visible.length-1]){
        //            sync1.trigger("owl.goTo", num2 - sync1visible.length+2)
        //        }else{
        //            if(num2 - 1 === -1){
        //                num2 = 0;
        //            }
        //            sync1.trigger("owl.goTo", num2);
        //        }
        //    } else if(num2 === sync1visible[sync1visible.length-1]){
        //        sync1.trigger("owl.goTo", sync1visible[1])
        //    } else if(num2 === sync1visible[0]){
        //        sync1.trigger("owl.goTo", num2-1)
        //    }
        //
        //}

        if(sync1 && sync2){
            if(sync1.hasClass("ct-js-owl--propertySlider1")){
                sync1.owlCarousel({
                    singleItem : true,
                    slideSpeed : 1000,
                    pagination: true,
                    navigation: true,
                    navigationText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                   afterAction : syncPosition,
                    responsiveRefreshRate : 200
                    //afterInit : function(el){
                    //    el.find(".owl-item").eq(0).addClass("syncedMain");
                    //}
                });
            }
            else{
                $(sync1).each(function(){
                    sync1.owlCarousel({
                        singleItem : true,
                        slideSpeed : 1000,
                        pagination:false,
                       afterAction : syncPosition,
                        responsiveRefreshRate : 200
                    });
                });

            }
            if(sync2.hasClass("ct-js-owl--propertySlider2")){
                sync2.owlCarousel({
                    singleItem : true,
                    slideSpeed : 1000,
                    navigation: false,
                    navigationText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                    pagination:false,
                   // afterAction : syncPosition2,
                    responsiveRefreshRate : 100
                    //afterInit : function(el){
                    //    el.find(".owl-item").eq(0).addClass("synced");
                    //}
                });
            }
            else{
                $(sync2).each(function(){
                    sync2.owlCarousel({
                        items : 5,
                        itemsDesktop      : [1199,4],
                        itemsDesktopSmall     : [979,4],
                        itemsTablet       : [768,5],
                        itemsMobile       : [479,3],
                        navigation: true,
                        navigationText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                        pagination:false,
                        responsiveRefreshRate : 100,
                        afterInit : function(el){
                            el.find(".owl-item").eq(0).addClass("synced");
                        }
                    });
                });
                sync2.on("click", ".owl-item", function(e){
                    e.preventDefault();
                    var number = $(this).data("owlItem");
                    sync1.trigger("owl.goTo",number);
                });
            }
        }
    });

    /* ==== GOOGLE MAP ==== */

    var mapStyles = [{"featureType":"administrative","elementType":"labels.text.fill","stylers":[{"color":"#444444"}]},{"featureType":"landscape","elementType":"all","stylers":[{"color":"#f2f2f2"}]},{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"all","stylers":[{"saturation":-100},{"lightness":45}]},{"featureType":"road.highway","elementType":"all","stylers":[{"visibility":"simplified"}]},{"featureType":"road.arterial","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"all","stylers":[{"color":"#425a68"},{"visibility":"on"}]}];

    function initmap() {

        if (($(".ct-js-googleMap").length > 0) && (typeof google === 'object' && typeof google.maps === 'object')) {

            var draggable = true;

            if (device.mobile() || device.tablet()) {
                draggable = false;
            }

            $('.ct-js-googleMap--single').each(function () {
                var atcenter = "";
                var $this = $(this);
                var location = $this.data("location");
                var zoom = $this.data("zoom");
                var icongmap = $this.attr('data-icon');
                var markerDraggable = parseBoolean($this.attr('data-markerDraggable'), false);
                var offset = -30;
                var offsety = -20;
                var autoGPSselector = $('.ct-latlngAuto');
                var autoGPSlat = autoGPSselector.find('.latidude');
                var autoGPSlng = autoGPSselector.find('.longitude');

                if(markerDraggable!=true){
                    markerDraggable = false
                }

                if (validatedata($this.data("offset"))) {
                    offset = $this.data("offset");
                }

                if (validatedata($this.data("offsety"))) {
                    offsety = $this.data("offsety");
                }

                if (validatedata(location)) {
                    $this.gmap3({
                        marker: {
                            //latLng: [40.616439, -74.035540],
                            address: location, options: {
                                //visible: false
                                draggable: markerDraggable,
                                icon: new google.maps.MarkerImage(icongmap)
                            }, callback: function (marker) {
                                atcenter = marker.getPosition();
                                autoGPSlat.val(marker.getPosition().lat());
                                autoGPSlng.val(marker.getPosition().lng());
                                google.maps.event.addListener(marker, 'drag', function() {
                                    autoGPSlat.val(marker.getPosition().lat());
                                    autoGPSlng.val(marker.getPosition().lng())
                                });
                            }
                        }, map: {
                            options: {
                                //maxZoom:11,
                                zoom: zoom,
                                styles:mapStyles,
                                mapTypeId: google.maps.MapTypeId.ROADMAP, // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                scrollwheel: false,
                                disableDoubleClickZoom: false,
                                draggable: draggable, //disableDefaultUI: true,
                                disableDefaultUI: true,
                                mapTypeControlOptions: {
                                    //mapTypeIds: [google.maps.MapTypeId.ROADMAP, google.maps.MapTypeId.HYBRID],
                                    //style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                                    //position: google.maps.ControlPosition.RIGHT_CENTER
                                    mapTypeIds: []
                                }
                            }, events: {
                                idle: function () {
                                    if (!$this.data('idle')) {
                                        $this.gmap3('get').panBy(offset, offsety);
                                        $this.data('idle', true);
                                    }
                                }
                            }
                        }, overlay: {
                            address: location, options: {
                                offset: {
                                    y: -100, x: -25
                                }
                            }
                        }
                        //},"autofit"
                    });

                    // center on resize
                    google.maps.event.addDomListener(window, "resize", function () {
                        //var userLocation = new google.maps.LatLng(53.8018,-1.553);
                        setTimeout(function () {
                            $this.gmap3('get').setCenter(atcenter);
                            $this.gmap3('get').panBy(0, offset);
                        }, 400);

                    });

                    // set height

                    if($this.hasClass("ct-googleMap-2col") && (device.mobile() || device.tablet())){
                        $this.css("min-height", "600px");
                    }else{
                        $this.css("min-height", $this.data("height") + "px");
                    }
                }

                if ($this.parent().parent().hasClass('hidemap')) {
                    $this.parent().animate({height: '0px'}, 500);
                }

            }),
                jQuery('.ct-js-googleMap--group').each(function () {
                    var $this = jQuery(this);
                    var $display_desc = validatedata(parseBoolean($this.attr("data-display-desc")), false);
                    var dataMarkers= [];

                    if($display_desc == false){
                        $this.gmap3({
                            map:{
                                options:{
                                    center:[40.742803, -74.002424],
                                    zoom: 14,
                                    scrollwheel: false,
                                    disableDoubleClickZoom: false,
                                    draggable: draggable, //disableDefaultUI: true,
                                    disableDefaultUI: true,
                                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                                    // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                    styles:mapStyles
                                }
                            },
                            marker:{
                                values: [
                                    {
                                        address:"301 w 4th Street, New York",
                                        options:{
                                            icon: "assets/images/marker-villa.png"
                                        }
                                    },
                                    {
                                        address:"128 7th Ave S, New York",
                                        options:{
                                            icon: "assets/images/marker-apartment.png"
                                        }
                                    },
                                    {
                                        address:"Eve 55 W 8th St, New York",
                                        options:{
                                            icon: "assets/images/marker-commercial.png"
                                        }
                                    },
                                    {
                                        address:"21 W 16th St New York",
                                        options:{
                                            icon: "assets/images/marker-flat.png"
                                        }
                                    },
                                    {
                                        address:"Washington Square Fountain, New York",
                                        options:{
                                            icon: "assets/images/marker-house.png"
                                        }
                                    },
                                    {
                                        address:"Pinkberry - Chelsea 170 8th Ave, New York",
                                        options:{
                                            icon: "assets/images/marker-land.png"
                                        }
                                    },
                                    {
                                        address:"8 Charles Ln New York",
                                        options:{
                                            icon: "assets/images/marker-apartment.png"
                                        }
                                    },
                                    {
                                        address:"74 Green St Brooklyn",
                                        options:{
                                            icon: "assets/images/marker-commercial.png"
                                        }
                                    },

                                    {
                                        address:"321 w 4th Street, New York",
                                        options:{
                                            icon: "assets/images/marker-house.png"
                                        }
                                    }
                                ],
                                cluster:{
                                    radius: 50,
                                    0: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 53,
                                        height: 52
                                    },
                                    2: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 56,
                                        height: 55
                                    },
                                    50: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 66,
                                        height: 65
                                    }
                                }
                            }
                        })
                    } else{
                        $this.gmap3({
                            map:{
                                options:{
                                    center:[40.742803, -74.002424],
                                    zoom: 14,
                                    scrollwheel: false,
                                    disableDoubleClickZoom: false,
                                    draggable: draggable, //disableDefaultUI: true,
                                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                                    disableDefaultUI: true,
                                    styles:mapStyles
                                    // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                },
                                events:{
                                    click: function(map, event, context){
                                        gmap_clear_markers();
                                    }
                                }
                            }
                        })

                        //Ajax for JSon file
                        $.ajax({
                            url: "assets/js/gmaps/json/markers.json",
                            dataType: 'json',
                            type: 'POST',
                            success: function(data) {
                                dataMarkers = data.markers;
                                $.each(dataMarkers, function(key, val) {
                                    $this.gmap3({
                                        marker:{
                                            values:[{
                                                address:val.address,
                                                options:{
                                                    icon: val.icon
                                                },
                                                events: {
                                                    click: function() {
                                                        gmap_clear_markers();
                                                        $this.gmap3({
                                                            overlay:{
                                                                address:val.address,
                                                                options:{
                                                                    content: "<div class='ct-itemProducts ct-hover ct-itemProducts--boxed ct-gmapProduct animated activate fadeInDownSmall'>"+
                                                                    "<a href='product-single.html'>"+
                                                                    "<div class='ct-main-content'>" +
                                                                    "<div class='ct-imageBox'>"+
                                                                    "<img src='"+val.image+"' alt=''>"+
                                                                    "<i class='fa fa-eye'></i>"+
                                                                    "</div>"+
                                                                    "<div class='ct-main-text'>"+
                                                                    "<div class='ct-product--tilte'>"+
                                                                    val.address+
                                                                    "</div>"+
                                                                    "<div class='ct-product--price'>"+
                                                                    "<span>$ "+val.price+"</span>"+
                                                                        //"<span class='ct-price--Old'>$ 450,000</span>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "<div class='ct-product--meta'>"+
                                                                    "<div class='ct-status'><span class='ct-fw-600'>Status</span> "+val.status+"</div>"+
                                                                    "<div class='ct-icons'>"+
                                                                    "<span>"+
                                                                    "<i class='fa fa-bed'></i> "+
                                                                    val.bedrooms+
                                                                    "</span>"+
                                                                    "<span>"+
                                                                    "<i class='fa fa-cutlery'></i> "+
                                                                    val.bathrooms+
                                                                    "</span>"+
                                                                    "</div>"+
                                                                    "<div class='ct-text'>"+
                                                                    "<span> Area: <span>"+val.area+" m2</span></span>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "<div class='ct-bottomArrow'></div>"+
                                                                    "</a>"+
                                                                    "</div>",
                                                                    offset:{
                                                                        y:-340,
                                                                        x:-140
                                                                    }
                                                                }
                                                            }

                                                        });
                                                    }
                                                }
                                            }],
                                            cluster:{
                                                radius: 20,
                                                0: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 53,
                                                    height: 52
                                                },
                                                2: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 56,
                                                    height: 55
                                                },
                                                50: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 66,
                                                    height: 65
                                                }
                                            }
                                        }
                                    });
                                });

                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                console.log('ERROR', textStatus, errorThrown);
                            }
                        });

                    };
                    // Function Clear Markers
                    function gmap_clear_markers() {
                        $('.ct-gmapProduct').each(function() {
                            $(this).remove();
                        });
                    }


                    var map = $(".ct-js-googleMap").gmap3({
                        get: {
                            name:"map"
                        }
                    });

                    //Navigation

                    $('#zoomin').on("click", function(){
                        var newCenter = map.getZoom();
                        map.setZoom(newCenter+1);
                    })

                    $('#zoomout').on("click", function(){
                        var newCenter = map.getZoom();
                        map.setZoom(newCenter-1);
                    })

                    $('#geolocation').on("click", function(){
                        // Try HTML5 geolocation
                        if(navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(function(position) {
                                var pos = new google.maps.LatLng(position.coords.latitude,
                                    position.coords.longitude);

                                $(".ct-js-googleMap").gmap3({
                                    circle:{
                                        options:{
                                            center: pos,
                                            radius : 800,
                                            fillColor : "#60a7d4",
                                            strokeColor : "#333333"
                                        },
                                        callback: function(){
                                            $(this).gmap3('get').setZoom(15);
                                        }
                                    }
                                });

                                map.setCenter(pos);
                            }, function() {
                                handleNoGeolocation(true);
                            });
                        } else {
                            // Browser doesn't support Geolocation
                            handleNoGeolocation(false);
                        }
                    })

                    function handleNoGeolocation(errorFlag) {
                        if (errorFlag) {
                            var content = 'Error: The Geolocation service failed.';
                        } else {
                            var content = 'Error: Your browser doesn\'t support geolocation.';
                        }
                    }

                    function searchauto() {

                        var locations = [];

                        // Create the search box and link it to the UI element.
                        var input = (document.getElementById('searchGmaps'));

                        var searchBox = new google.maps.places.SearchBox(
                            /** @type {HTMLInputElement} */(input));

                        // Listen for the event fired when the user selects an item from the
                        // pick list. Retrieve the matching places for that item.

                        google.maps.event.addListener(searchBox, 'places_changed', function() {
                            var places = searchBox.getPlaces();


                            if (places.length == 0) {
                                return;
                            }
                            for (var i = 0, location; location = locations[i]; i++) {
                                location.setMap(null);
                            }

                            // For each place, get the icon, place name, and location.

                            locations = [];
                            var bounds = new google.maps.LatLngBounds();
                            for (var i = 0, place; place = places[i]; i++) {
                                var image = {
                                    url: "assets/images/marker-land.png",
                                    //size: new google.maps.Size(71, 71),
                                    origin: new google.maps.Point(0, 0),
                                    anchor: new google.maps.Point(17, 34)
                                    //scaledSize: new google.maps.Size(25, 25)
                                };

                                bounds.extend(place.geometry.location);
                            }

                            map.fitBounds(bounds);
                        });

                        google.maps.event.addListener(map, 'bounds_changed', function() {
                            var bounds = map.getBounds();
                            searchBox.setBounds(bounds);
                        });
                    }
                    if($('.ct-searchGmaps').length != 0){
                        searchauto();
                    }
                    console.log($this)
                    // set height
                    if($this.hasClass("ct-googleMap-2col") && (device.mobile() || device.tablet())){
                        $this.css("min-height", "600px");
                    }else{
                        $this.css("min-height", $this.data("height") + "px");
                    }
                })
        }

    }

    initmap();

    //Extended search input in topbar // ----------------------------------------

    $(document).mouseup(function (e) {
        var $searchform = $(".ct-navbar-search");

        if(!$('#ct-js-navSearch').is(e.target)){
            if (!$searchform.is(e.target) // if the target of the click isn't the container...
                && $searchform.has(e.target).length === 0) // ... nor a descendant of the container
            {
                $navbarel.removeClass('is-inactive');
                $searchform.fadeOut();
            }
        }
    });

    // Navigation in Privacy Policy // -----------------------------------

    $(window).scroll(function() {
        $(".ct-navigation").each(function () {
            var navigationsmall = $('.ct-navigation');
            var footerForNavigation = $('footer');

            if (navigationsmall.offset().top + navigationsmall.height() >= footerForNavigation.offset().top - 10){
                navigationsmall.css('position', 'absolute');
            }
            if ($(document).scrollTop() + window.innerHeight - 200 < footerForNavigation.offset().top){
                navigationsmall.css('position', 'fixed'); // restore when you scroll up
            }
        });
    });

    $(window).on('resize', function() {
        if ($(window).width() < 768) {
            snapper.enable();
        } else{
            snapper.close();
            snapper.disable();
        }
    })

})(jQuery);