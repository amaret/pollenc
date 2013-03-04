<?php  

require_once "./mongostore.class.php";
date_default_timezone_set('America/Los_Angeles');            # We need this called for datetime

$store = new MongoStore();

function emailExists($email) {
  global $store;  
  $rec = $store->findOne('clc.tokens', array("email" => $email));  
  return $rec != null;
}

function newToken($email) {
  global $store;
  $vid = '';
  do { 
    $vid = generateVid();
  } while ($store->findOne('clc.tokens', array("vid" => $vid)) != null);  

  $t = array("vid" => $vid, "email" => $email, "token" => "", "active" => false, "entered" => new DateTime());
  $store->save('clc.tokens', $t);  
  return $vid;
}

function validateEmail($vid) {
  global $store;
  $rec = $store->findOne('clc.tokens', array('vid' => $vid));
  
  if ($rec != null) {
    if ($rec['token'] != '') {
      return array("result" => "error", "error" => "This email has already been validated"); ;
    } else {
      $t = generateToken();
      $rec['token'] = $t;
      $rec['active'] = true;
      $rec['activated'] = new DateTime();
      $store->update('clc.tokens', array("vid" => $vid), $rec);      
      $r = sendTokenEmail($rec['email'], $t);
      
      if ($r == "ok") {
        return array("result" => "ok", "token" => $t);
      } else {
        return array("result" => "error", "error" => $r);
      }
    }
  } else {
    return array("result" => "error", "error" => "The validation id was not found.");
  }
  
}

function sendValidationEmail($to, $vid) {
  $from = "Amaret Pollen <info@wind.io>";
  $subject = "Pollen email validation";
  $body =  "Thank you for your interest in using pollen.\n";
  $body .= "To receive your access token, please validate your email: http://localhost/w2/pollen?vid=" . $vid . "\n\n\n";
  $body .= "--\nAmaret, Inc.\nhttp://pollen.wind.io";

  return sendEmail($from, $to, $subject, $body);
}

function sendTokenEmail($to, $token) {
  $from = "Amaret Pollen <info@wind.io>";
  $subject = "Your pollen compiler token";
  $body =  "You now have access to use the pollen compiler. For help using the compiler, see the docs at (todo).\n";
  $body .= "Your access token is: " . $token . "\n\n";
  $body .= "--\nAmaret, Inc.\nhttp://pollen.wind.io";

  return sendEmail($from, $to, $subject, $body);  
}

function sendEmail($from, $to, $subject, $body) {
  $host = "email-smtp.us-east-1.amazonaws.com";
  $username = "AKIAJ5S2KOOFTYV6B7PA";
  $password = "AhdNBd175AnxMA69joKnMkDm5pZntjlIqTbA5nLf3Ro5";

  $headers = array ('From' => $from, 'To' => $to, 'Subject' => $subject);
  $smtp = Mail::factory('smtp', array ('host' => $host, 'auth' => true, 
                                      'username' => $username, 'password' => $password));

  $mail = $smtp->send($to, $headers, $body);

  if (PEAR::isError($mail)) {
    return $mail->getMessage();
  } else {
    return "ok";
  }  
}

function generateVid() { return genid(8); }
function generateToken() { return genid(12); }

function genid($len) {
  $charset='abcdefghijklmnopqrstuvwxyz0123456789';
  $str = '';
  $count = strlen($charset) - 1;
  while ($len--) {
    $str .= $charset[mt_rand(0, $count)];
  }
  return $str;  
}


// function generateToken() {
//   $charset='abcdefghijklmnopqrstuvwxyz0123456789';
//   $length = 12;
//   $str = '';
//   $count = strlen($charset) - 1;
//   while ($length--) {
//     $str .= $charset[mt_rand(0, $count)];
//   }
//   return $str;
// }


?>

