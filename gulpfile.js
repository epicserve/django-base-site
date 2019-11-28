const { src, dest, parallel, watch: gulpWatch, task } = require('gulp'),
      babel = require('gulp-babel'),
      livereload = require('gulp-livereload'),
      rename = require('gulp-rename'),
      sass = require('gulp-sass'),
      sourcemaps = require('gulp-sourcemaps'),
      uglify = require('gulp-uglify');

const config = {
  boostrap_sass_dir: './node_modules/bootstrap/scss',
  scss_src_path: './src/scss/**/*.scss',
  css_dist_path: './public/static/css',
  js_src_path: './src/js/**/*.js',
  js_dist_path: './public/static/js',
};

function css() {

  const path = (typeof arguments[0] === 'string') ? arguments[0] : config.scss_src_path;

  return src(path)
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
    .pipe(livereload());
}

function js() {
	return src(config.js_src_path)
		.pipe(babel({
			presets: ['@babel/preset-env']
		}))
    .pipe(uglify())
    .pipe(rename({
      suffix: '.min'
    }))
		.pipe(dest(config.js_dist_path));
}

function watch() {
  livereload.listen({start: true});
  return gulpWatch(config.scss_src_path)
    .on('change', (file) => {
      return css(file)
    });
}

task(js, css);

exports.css = css;
exports.js = js;
exports.watch = watch;
exports.default = parallel(css, js, watch);
