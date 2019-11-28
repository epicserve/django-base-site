const { src, dest, parallel } = require('gulp'),
      rename = require('gulp-rename'),
      sass = require('gulp-sass'),
      sourcemaps = require('gulp-sourcemaps');

const config = {
  boostrap_sass_dir: './node_modules/bootstrap/scss',
  scss_src_path: './src/scss/**/*.scss',
  css_dist_path: './public/static/css',
};

function css() {
  return src(config.scss_src_path)
    .pipe(sourcemaps.init())
      .pipe(sass({
        outputStyle: 'compressed',
        includePaths: [config.boostrap_sass_dir]
      }))
      .pipe(rename({
        suffix: '.min'
      }))
    .pipe(sourcemaps.write('maps', {
      includeContent: true,
      sourceRoot: config.scss_src_path
    }))
    .pipe(dest(config.css_dist_path))
}

exports.css = css;
exports.default = parallel(css);
