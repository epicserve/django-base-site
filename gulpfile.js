var browser = require("gulp-browser");
var del = require('del');
var gulp = require('gulp');
var livereload = require('gulp-livereload');
var rename = require('gulp-rename');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var debug = require('gulp-debug');

var config = {
  boostrap_sass_dir: './node_modules/bootstrap/scss',
  js_source: './src/js/**/*.js',
  static_css_dir: './public/static/css',
  static_js_dir: './public/static/js'
};

gulp.task('clean', function () {
  return del([
    config.static_css_dir,
    config.static_js_dir
  ]);
});

gulp.task('build', ['clean'], function() {
  var stream = gulp.src(config.js_source)
    .pipe(browser.browserify())
    .pipe(gulp.dest(config.static_js_dir));
  return stream;
});

gulp.task('sass', ['clean'], function () {
  gulp.src('./src/scss/**/*.scss')
    .pipe(debug({title: 'unicorn:'}))
    .pipe(sourcemaps.init())
    .pipe(sass({
      outputStyle: 'compressed',
      includePaths: [config.boostrap_sass_dir]
    }).on('error', sass.logError))
    .pipe(rename({
      suffix: '.min'
    }))
    .pipe(sourcemaps.write('maps', {
      includeContent: true,
      sourceRoot: config.static_css_dir
    }))
    .pipe(gulp.dest(config.static_css_dir))
    .pipe(livereload());
});

gulp.task('watch', function () {
  livereload.listen();
  gulp.watch('./src/js/**/*.js', ['build']);
  gulp.watch('./src/scss/**/*.scss', ['sass']);
  gulp.watch('./*.html').on('change', livereload.changed);
});

gulp.task('default', ['sass', 'build', 'watch']);
