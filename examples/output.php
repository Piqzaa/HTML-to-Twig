<?php
/**
 * Template Name: Custom Page Template
 *
 * @package mysite
 */

get_header();
?>


<!-- Header -->
<header class="site-header" id="header">
<div class="container">
<a class="logo" href="index.html">
<img alt="Company Logo" src="<?php echo esc_url(get_template_directory_uri() . '/images/logo.png'); ?>"/>
</a>
<!-- Main Navigation -->
<nav class="main-nav"><?php
wp_nav_menu(array(
    'theme_location' => 'main_nav',
    'menu_class'     =&gt; 'nav-menu',
    'container'      =&gt; false,
    'fallback_cb'    =&gt; false,
));
?></nav>
</div>
</header>
<!-- Hero Section -->
<section class="hero" style="background-image: url('<?php echo esc_url(get_template_directory_uri() . '/images/hero-bg.jpg'); ?>');">
<div class="container">
<h1>Welcome to Our Website</h1>
<p>We create amazing digital experiences</p>
<a class="btn btn-primary" href="contact.html">Get Started</a>
</div>
</section>
<!-- Main Content -->
<main class="site-main" id="content" role="main">
<div class="container">
<!-- Services Section -->
<section class="services">
<h2>Our Services</h2>
<div class="row">
<article class="service-card">
<img alt="Web Development" src="<?php echo esc_url(get_template_directory_uri() . '/images/service-1.png'); ?>"/>
<h3>Web Development</h3>
<p>Custom websites built with modern technologies.</p>
</article>
<article class="service-card">
<img alt="Mobile Apps" src="<?php echo esc_url(get_template_directory_uri() . '/images/service-2.png'); ?>"/>
<h3>Mobile Apps</h3>
<p>Native and cross-platform mobile applications.</p>
</article>
<article class="service-card">
<img alt="UI/UX Design" src="<?php echo esc_url(get_template_directory_uri() . '/images/service-3.png'); ?>"/>
<h3>UI/UX Design</h3>
<p>Beautiful and intuitive user interfaces.</p>
</article>
</div>
</section>
<!-- Team Section -->
<section class="team">
<h2>Our Team</h2>
<div class="team-grid">
<div class="team-member">
<img alt="John Doe" src="<?php echo esc_url(get_template_directory_uri() . '/images/team/john.jpg'); ?>"/>
<h4>John Doe</h4>
<p>CEO &amp; Founder</p>
</div>
<div class="team-member">
<img alt="Jane Smith" src="<?php echo esc_url(get_template_directory_uri() . '/images/team/jane.jpg'); ?>"/>
<h4>Jane Smith</h4>
<p>Lead Developer</p>
</div>
<div class="team-member">
<img alt="Mike Johnson" src="<?php echo esc_url(get_template_directory_uri() . '/images/team/mike.jpg'); ?>"/>
<h4>Mike Johnson</h4>
<p>Designer</p>
</div>
</div>
</section>
</div>
</main>
<!-- Sidebar -->
<aside class="sidebar" role="complementary">
<div class="widget">
<h3>Recent Posts</h3>
<ul>
<li><a href="blog/post-1.html">How to Build a Website</a></li>
<li><a href="blog/post-2.html">Design Tips for 2024</a></li>
<li><a href="blog/post-3.html">Mobile-First Development</a></li>
</ul>
</div>
</aside>
<!-- Footer -->
<footer class="site-footer" id="footer" role="contentinfo">
<div class="container">
<div class="footer-nav">
<nav class="menu"><?php
wp_nav_menu(array(
    'theme_location' => 'menu',
    'menu_class'     =&gt; 'menu',
    'container'      =&gt; false,
    'fallback_cb'    =&gt; false,
));
?></nav>
</div>
<p>© 2024 Company Name. All rights reserved.</p>
</div>
</footer>
<!-- Scripts -->
<script src="<?php echo esc_url(get_template_directory_uri() . '/js/jquery.min.js'); ?>"></script>
<script src="<?php echo esc_url(get_template_directory_uri() . '/js/scripts.js'); ?>"></script>
<script src="<?php echo esc_url(get_template_directory_uri() . '/js/custom.js'); ?>"></script>


<?php
get_sidebar();
get_footer();
