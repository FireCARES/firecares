/*
By Lucas Fajger

What we needa here!
---------------------------
1.CSS

 Navbar scroll top class u should style on your own how width are your fixed elements, if they are not witdh from top: 0, left: 0 then we remove left:0;
 .navbar-scroll-top {
 position: fixed;
 left: 0;
 top: 0;
 width: 100%;
 z-index: 9999;
 }

 //headroom styles for fixed headers and menus
 .headroom {
 transition: transform 200ms linear;
 z-index: 9998;
 }
 .headroom--pinned {
 transform: translateY(0%);
 display: block;
 }
 .headroom--unpinned {
 transform: translateY(-100%);
 display: none;
 }

2. CLASSES inside tags - required
 For topBar - ct-topBar  <div class="ct-topBar">
 For menu - navbar <nav class="navbar"> - no matter if it's nav or div :)

2.1 Classes in Body we use for different variations

 Body classes Navbars/TopBars:

 ct-headroom--scrollUpMenu
 ct-headroom--scrollUpTopBar
 ct-headroom--scrollUpBoth
 ct-headroom--fixedTopBar
 ct-headroom--fixedMenu
 ct-headroom--fixedBoth
 ct-headroom--hideMenu

 <body class="ct-headroom--fixedBoth">


3. if you dont have in your main.js $topbarel and $navbarel and $bodyel variables then copy them at the beggining in this function:

 var $bodyel = jQuery("body");
 var $navbarel = jQuery(".navbar");
 var $topbarel = jQuery(".ct-topBar");


4. if you dont have the function validate in main js, copy this before this init

 function validatedata($attr, $defaultValue) {
 "use strict";
 if ($attr !== undefined) {
 return $attr
 }
 return $defaultValue;
 }

TIP: If you have both elements with this effect deployed in main html then good practise is set the same offset for the both elements
TIP: We have default values as data attributes, but if you mind you can change it on your own:
EXAMPLE: <div class="ct-topBar" data-starttopbar=300 data-offset="500">

 */

(function($){
    "use strict";

    $(document).ready(function () {
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
    });
})(jQuery);
