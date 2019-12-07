import 'jquery';
import 'bootstrap';

import jQuery from 'jquery';
window.$ = window.jQuery = jQuery;

const myArr = [1, 2, 3].map((n) => n + 1);
if (myArr.toString() !== '2,3,4') {
  console.error("Array didn't transpile.");
}
if ($().modal === undefined) {
  console.error("Bootstrap wasn't imported correctly.");
}
