var gulp = require('gulp');
var livereload = require('gulp-livereload');
var rename = require('gulp-rename');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');


var config = {
    boostrap_sass_dir: './node_modules/bootstrap-sass/assets/stylesheets',
    static_css_dir: './static/css',
};


gulp.task('sass', function () {
  gulp.src('./static/scss/**/*.scss')
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
  gulp.watch('./static/scss/**/*.scss', ['sass']);
  gulp.watch('./**/*.html').on('change', livereload.changed);
});


gulp.task('default', ['sass', 'watch']);
