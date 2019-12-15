import jQuery from 'jquery';
import 'bootstrap';

const $ = jQuery,
  myArr = [1, 2, 3].map((n) => n + 1);

window.$ = jQuery;
window.jQuery = jQuery;

if (myArr.toString() !== '2,3,4') {
  console.error("Array didn't transpile.");
}

if ($().modal === undefined) {
  console.error("Bootstrap wasn't imported correctly.");
}
