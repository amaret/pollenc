<?php

$__MONGO_HOST = "localhost"; //"redbis.wind.io";
$__SITE_URL = "http://pollen.wind.io/tokens";

require_once "Mail.php";
require_once "./access.php";

$error = '';
$message = '';

if (isset($_GET['email'])) {
  if (emailExists($_GET['email'])) {
      $error = "This user has already generated a token.";
  } else {
    $vid = newToken($_GET['email']);
    $r = sendValidationEmail($_GET['email'], $vid);
    
    if ($r == 'ok') { 
      $message = "An email has been sent.";
    } else { 
      removeVid($vid);
      $error = $r; 
    }
  }
} else if (isset($_GET['vid'])) {
  $ret = validateEmail($_GET['vid']);
  
  if ($ret['result'] == "ok") {
    $message = "Your access token is: " . $ret['token'];
  } else {
    $error = $ret['error'];
  }
}  

?>


<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Pollen</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- CSS -->
    <link href="assets/css/bootstrap.css" rel="stylesheet">
    <style type="text/css">

      /* Sticky footer styles
      -------------------------------------------------- */

      html,
      body {
        height: 100%;
        /* The html and body elements cannot have any padding or margin. */
      }

      /* Wrapper for page content to push down footer */
      #wrap {
        min-height: 100%;
        height: auto !important;
        height: 100%;
        /* Negative indent footer by it's height */
        margin: 0 auto -60px;
      }

      /* Set the fixed height of the footer here */
      #push,
      #footer {
        height: 60px;
      }
      #footer {
        background-color: #f5f5f5;
      }

      /* Lastly, apply responsive CSS fixes as necessary */
      @media (max-width: 767px) {
        #footer {
          margin-left: -20px;
          margin-right: -20px;
          padding-left: 20px;
          padding-right: 20px;
        }
      }



      /* Custom page CSS
      -------------------------------------------------- */
      /* Not required for template or sticky footer method. */

      .container {
        width: auto;
        max-width: 680px;
      }
      .container .credit {
        margin: 20px 0;
      }

    </style>
    <link href="assets/css/bootstrap-responsive.css" rel="stylesheet">
  </head>

  <body>

    <!-- Part 1: Wrap all page content here -->
    <div id="wrap">

      <!-- Begin page content -->
      <div class="container">
        <div class="page-header">
          <h1>Pollen Cloud Compiler Access</h1>
        </div>

        <p class="lead">Submit and validate your email to get an access token.</p>
        
        <form class="form-inline offset1" method="get" action="">
          <input style="height: 34px; font-size: 17.5px" class="input-xxlarge span3" type="text" placeholder="Your email" name="email">
          <button type="submit" class="btn btn-warning btn-large">Submit</button>
        </form>

        <div>
          <p class="lead">
            <?php
              if ($error != '') { echo $error; }
              else if ($message != '') { echo $message; }
            ?>
          </p>
        </div>

      </div>

      <div id="push"></div>
    </div>

    <div id="footer">
      <div class="container">
        <p class="muted credit">&copy; <a href="http://amaret.com">Amaret, Inc.</a> 2013</p>
      </div>
    </div>



    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->

<!--     <script src="assets/js/jquery.js"></script>
    <script src="assets/js/bootstrap-transition.js"></script>
    <script src="assets/js/bootstrap-alert.js"></script>
    <script src="assets/js/bootstrap-modal.js"></script>
    <script src="assets/js/bootstrap-dropdown.js"></script>
    <script src="assets/js/bootstrap-scrollspy.js"></script>
    <script src="assets/js/bootstrap-tab.js"></script>
    <script src="assets/js/bootstrap-tooltip.js"></script>
    <script src="assets/js/bootstrap-popover.js"></script>
    <script src="assets/js/bootstrap-button.js"></script>
    <script src="assets/js/bootstrap-collapse.js"></script>
    <script src="assets/js/bootstrap-carousel.js"></script>
    <script src="assets/js/bootstrap-typeahead.js"></script>
 -->
  </body>
</html>
