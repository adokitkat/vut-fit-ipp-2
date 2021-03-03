<?php
  # Print CSS
  function print_css() {
    echo '
    body {text-align: center;}
    table {
      table-layout: fixed ;
      border-collapse: collapse;
      overflow-wrap: anywhere;
      width: 100% ;
    }
    td {
      width: 25% ;
    }
    table, th, td {
      border: 1px solid black;
    }
    .OK {
      background-color: green;
    }
    .ERROR {
      background-color: red;
    }';
  }

  # Prints top half of HTML
  function print_html_up($n) {
    $tested = [ 1 => '<i>parse.php</i>',
                2 => '<i>interpret.py</i>',
                3 => '<i>parse.php</i> and <i>interpret.py</i>'];
    echo '<!DOCTYPE html>
<html lang="en-US">
<head>
  <style>';
    print_css();
    echo PHP_EOL . '  </style>
  <meta charset="UTF-8">
  <title>test.php output</title>
</head>
<body>
' . "  <h1>Results of testing $tested[$n]</h1><br>
" . '  <table>
    <tr>
      <th>Filename</th>
      <th>Expected exit code</th>
      <th>Returned exit code</th> 
      <th>Status</th>
    </tr>
';
  }
  # Prints bottom half of HTML
  function print_html_down($correct, $all) {
    echo "  </table>
    <h2>Score: $correct / $all</h2>
</body>
</html>";
  }

  # Prints status and counts number of successful tests
  function print_status($status, &$correct, &$all){
    $all++;
    if ($status == 'OK') {
      $correct++;
      echo "      <th class='OK'>$status</th>
    </tr>";
    } elseif ($status == 'ERROR') {
      echo "      <th class='ERROR'>$status</th>
    </tr>";
    } else {
      echo "        <th>$status</th>
    </tr>";
    }
  }

  # Prints the body of HTML and runs the desired tests
  function print_body($option, $base_dir, $dirs, $parser, $interpret, $python, $PHP, $java, &$correct, &$all) {
    foreach($dirs as $dir) {
      foreach(glob($dir . '/*.src') as $f) {
        $file = realpath($f);
        $file_no_ext = substr($file, 0, -4);
        $file_rc = $file_no_ext . '.rc';
        $file_in = $file_no_ext . '.in';
        $file_out = $file_no_ext . '.out';

        # checks if files exist and if not, creates them
        if (!file_exists($file_in))  {
          $file_created = fopen($file_in, "w");
          fclose($file_created);
        }
        if (!file_exists($file_out)) {
          $file_created = fopen($file_out, "w");
          fclose($file_created);
        }
        if (!file_exists($file_rc))  {
          $file_created = fopen($file_rc, "w");
          fwrite($file_created, '0');
          fclose($file_created);
        }
        $file_created = fopen("$file_no_ext.tmp", "w");
        fclose($file_created);

        $tmp_exit = tempnam($dir, 'rc');
        $tmp = fopen($tmp_exit, 'w+');

        $exit_code = null;
        
        # parse only
        if ($option === 1) {
          exec("$PHP \"$parser\" < \"$file\" > \"$file_no_ext.tmp\"");
          exec("java -jar \"$java\" \"$file_no_ext.tmp\" \"$file_out\"", $null, $diff_exit);
        
        # interpret only
        } elseif ($option === 2) {
          exec("$python \"$interpret\" --source=\"$file\" < \"$file_in\" > \"$file_no_ext.tmp\"", $output, $exit_code);
          fwrite($tmp, $exit_code);
          fclose($tmp);
          exec("diff -qZ \"$file_rc\" \"$tmp_exit\"", $null, $diff_exit);
        
          # both
        } elseif ($option === 3) {
          $file_created = fopen("$file_no_ext.int_tmp", "w");
          fclose($file_created);

          exec("$PHP \"$parser\" < \"$file\" > \"$file_no_ext.int_tmp\"");
          exec("$python \"$interpret\" --source=\"$file_no_ext.int_tmp\" < \"$file_in\" > \"$file_no_ext.tmp\"", $output, $exit_code);
          fwrite($tmp, $exit_code);
          fclose($tmp);
          exec("diff -qZ \"$file_rc\" \"$tmp_exit\"", $null, $diff_exit);


          unlink("$file_no_ext.int_tmp");
        }

        unlink($tmp_exit);
        
        # checks diffs
        if ($diff_exit == 0) {
          if ($exit_code != 0) {
            $status = 'OK';
          } else {
            exec("diff -qZ \"$file_out\" \"$file_no_ext.tmp\"", $null, $diff_content);
            if ($diff_content == 0) {$status = 'OK';} else {$status = 'ERROR';}
          }
        } else {
          $status = 'ERROR';
        }
        unlink("$file_no_ext.tmp");

        $file_rc_handler = fopen($file_rc, "r");
        $file_rc_code = fread($file_rc_handler, 2);
        fclose($file_rc_handler);

        $name = substr(str_replace($base_dir, '', $file), 1);
        echo "
    <tr>
      <th>$name</th>
      <th>$file_rc_code</th>
      <th>$exit_code</th>
";      print_status($status, $correct, $all);
      }
    }
  }

  # Recursively scans directories and load their paths into an array
  function recursive_scan(&$all_dirs, $dir_path) {
    foreach(glob($dir_path . '/*', GLOB_ONLYDIR) as $dir) {
      array_push($all_dirs, $dir);
      recursive_scan($all_dirs, $dir);
    }
  }

  # Settings
  $python = 'python3.8';
  $PHP = 'php7.4';
  $dir_current = dirname(__FILE__);
  $dir_tests = $dir_current;
  $file_parser = realpath($dir_current . '/parse.php');
  $file_interpret = realpath($dir_current . '/interpret.py');
  $file_jexamxml = realpath('/pub/courses/ipp/jexamxml/jexamxml.jar');
  $recursive = false;
  $parse_only = false;
  $int_only = false;

  # Argument parsing
  $longopts = array(
    "help", "directory:", "recursive",
    "parse-script:", "int-script:",
    "parse-only", "int-only", "jexamxml:",
  );
  $arguments = getopt('', $longopts);

  if (array_key_exists('help', $arguments)) {
    echo 'Help...';
    exit(0);
  }
  if (array_key_exists('directory', $arguments))    {$dir_tests = $arguments['directory'];}
  if (array_key_exists('recursive', $arguments))    {$recursive = true;}
  if (array_key_exists('parse-script', $arguments)) {$file_parser = $arguments['parse-script'];}
  if (array_key_exists('int-script', $arguments))   {$dir_interpret = $arguments['int-script'];}
  if (array_key_exists('parse-only', $arguments))   {$parse_only = true;}
  if (array_key_exists('int-only', $arguments))     {$int_only = true;}
  if (array_key_exists('jexamxml', $arguments))     {$dir_jexamxml = $arguments['jexamxml'];}

  if (($parse_only == true and $int_only == true)
    or ($parse_only == true and array_key_exists('int-script', $arguments))
    or ($int_only == true and array_key_exists('parse-script', $arguments))
  ) {exit(10);}

  $all_dirs = array($dir_tests);
  
  if ($recursive == true) {recursive_scan($all_dirs, $dir_tests);}
  
  $correct = 0;
  $all = 0;
  if ($parse_only == true) {
    $option = 1;
  } elseif ($int_only == true) {
    $option = 2;
  } else {
    $option = 3;
  }
  
  # Start of HTML printing
  print_html_up($option);
  print_body($option, $dir_tests, $all_dirs, $file_parser, $file_interpret, $python, $PHP, $file_jexamxml, $correct, $all);
  print_html_down($correct, $all);
  exit(0);
?>