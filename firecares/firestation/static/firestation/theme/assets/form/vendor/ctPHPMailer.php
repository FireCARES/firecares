<?php
require_once dirname(__FILE__) . '/class.phpmailer.php';

/**
 * Wrapper which extends PHPMailer settings
 * @author alex
 */
class ctPHPMailer extends PHPMailer {

	/**
	 * Returns mail body
	 * @param string $templateName
	 * @param $post
	 * @param array $variables
	 * @param bool $addReplyTo
	 */

	public function setup($templateName, $post, $variables, $addReplyTo = true) {

		if (file_exists($templateName)) {
			$body = file_get_contents($templateName);
		} else {
			$body = $templateName;
		}

		//it may be already parse
		if ($variables) {
			$params = array();
			foreach ($variables as $name => $rules) {
				$params['{' . $name . '}'] = $this->getValueFromArray($name, $post, '');
			}

			$body = strtr($body, $params);
		}

		$this->MsgHTML($body);

		if ($addReplyTo && $this->getValueFromArray('email', $post, '')) {
			$this->AddReplyTo($post['email']);
		}
	}

	/**
	 * Validate all fields
	 * @param $msgs
	 * @param array $post
	 * @param string $namespace
	 * @return array
	 */

	public function validateDynamic($msgs, $post, $namespace = 'field') {
		$structure = array('errors' => array(), 'fields' => array());
		$errors = array();
		if ($values = $this->getValueFromArray($namespace, $post)) {
			foreach ($values as $label => $params) {
				//param nam may have either required or not
				$type = '';
				$value = '';
				$required = false;
				if (isset($params['required'])) {
					$d = $params['required'];

					$required = true;

					$type = key($d);
					$value = $d[$type];

					//required field
					if ($value == '') {
						$errors[$namespace . '[' . $label . ']'][] = $msgs['required_error'];
					}
				} elseif (isset($params['optional'])) {
					$d = $params['optional'];

					$type = key($d);
					$value = $d[$type];
				}

				//we validate email address
				if ($type) {
					switch (strtolower($type)) {
						case 'email':
							//html5 will enforce this field that's why we do not check is it required
							if (!$this->validateEmail($value)) {
								$errors[$namespace . '[' . $label . ']'] = $msgs['email_error'];
							}
							break;

					}
				}

				$structure['fields'][$label] = $value;
			}
		}

		$structure['errors'] = $errors;

		return $structure;
	}

	/**
	 * Validate data
	 * @param array $fields
	 * @param array $post
	 * @return array
	 */
	public function validate($fields, $post) {
		$errors = array();
		foreach ($fields as $name => $rules) {
			if ($rules['required'] && ($this->getValueFromArray($name, $post, '') == '')) {
				$errors[$name][] = $rules['required_error'];
			}

			//validate email
			if ($name == 'email') {
				$val = $this->getValueFromArray($name, $post, '');

				//field is not required and empty - let's leave it
				if ($val == '' && !isset($errors[$name])) {
					continue;
				}

				if (!$this->validateEmail($val)) {
					$errors[$name] = $rules['email_error'];
				}
			}
		}

		return $errors;
	}

	/**
	 * Returns data from array
	 * @param string $name
	 * @param array $array
	 * @param null $default
	 * @return mixed
	 */

	protected function getValueFromArray($name, $array, $default = null) {
		return isset($array[$name]) ? $array[$name] : $default;
	}

	/**
	 * Validate email
	 * @param string $value
	 * @return bool|mixed
	 */
	protected function validateEmail($value) {
		$value = (string)$value;
		$valid = filter_var($value, FILTER_VALIDATE_EMAIL);

		if ($valid) {
			$host = substr($value, strpos($value, '@') + 1);

			if (version_compare(PHP_VERSION, '5.3.3', '<') && strpos($host, '.') === false) {
				// Likely not a FQDN, bug in PHP FILTER_VALIDATE_EMAIL prior to PHP 5.3.3
				$valid = false;
			}
		}
		return $valid;
	}
}
