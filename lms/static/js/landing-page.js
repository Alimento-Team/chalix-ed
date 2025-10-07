// Landing Page Interactive Features using RequireJS
require(['jquery'], function($) {
    'use strict';
    
    $(document).ready(function() {
        // Smooth scrolling for anchor links
        $('a[href^="#"]').on('click', function(event) {
            var target = $(this.getAttribute('href'));
            if(target.length) {
                event.preventDefault();
                $('html, body').stop().animate({
                    scrollTop: target.offset().top - 80
                }, 1000);
            }
        });
        
        // Add animation to feature cards on scroll
        function animateOnScroll() {
            $('.feature-card, .category-card, .success-card').each(function() {
                var elementTop = $(this).offset().top;
                var elementBottom = elementTop + $(this).outerHeight();
                var viewportTop = $(window).scrollTop();
                var viewportBottom = viewportTop + $(window).height();
                
                if (elementBottom > viewportTop && elementTop < viewportBottom) {
                    $(this).addClass('animate-in');
                }
            });
        }
        
        // Run animation check on scroll
        $(window).on('scroll', function() {
            animateOnScroll();
        });
        
        // Initial animation check
        animateOnScroll();
        
        // Add hover effects to buttons
        $('.btn-hero, .btn-large').hover(
            function() {
                $(this).addClass('hover-effect');
            },
            function() {
                $(this).removeClass('hover-effect');
            }
        );
    });
});
