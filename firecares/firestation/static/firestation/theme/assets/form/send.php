<?php
$ajax = (!empty($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) == 'xmlhttprequest');
$ajax = true;
//we do not allow direct script access
if (!$ajax) {
	//redirect to contact form
	echo "Please enable Javascript";
	exit;
}
require_once "config.php";

//we set up subject
$mail->Subject = isset($_REQUEST['email_subject']) ? $_REQUEST['email_subject'] : "Message from site";

//let's validate and return errors if required
$data = $mail->validateDynamic(array('required_error' => $requiredMessage, 'email_error' => $invalidEmail), $_REQUEST);

//let's make sure we have valid data
//if (!$data['errors'] && (!isset($_REQUEST['js']) || $_REQUEST['js'] != 1)) {
//$data['errors']['global'] = 'Javascript is required. Please try again';
//}

if ($data['errors']) {
	echo json_encode(array('errors' => $data['errors']));
	exit;
}

$html = '<body style="margin: 10px;">
<div style="width: 640px; font-family: Arial, Helvetica, sans-serif; font-size: 11px;">
  <h2>' . $mail->Subject . '</h2>
';

foreach ($data['fields'] as $label => $val) {
	$html .= '<p>' . $label . ': ' . $val . '</p>';
}

$html .= '</div></body>';

$mail->setup($html, $_REQUEST, array());

$result = array('success' => 1);
if (!$mail->Send()) {
	$result['success'] = 0;
}

echo json_encode($result);
exit;