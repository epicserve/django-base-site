const { dest, series, src, parallel, watch: gulpWatch } = require('gulp'),
      babel = require("babelify"),
      browserify = require("browserify"),
      buffer = require("vinyl-buffer"),
      del = require('del'),
      glob = require('glob'),
      livereload = require('gulp-livereload'),
      rename = require('gulp-rename'),
      sass = require('gulp-sass'),
      source = require("vinyl-source-stream"),
      sourcemaps = require('gulp-sourcemaps'),
      uglify = require('gulp-uglify');

const paths = {
  boostrapSassDir: './node_modules/bootstrap/scss',
  scssSrcPath: './src/scss/**/*.scss',
  cssDistDir: './public/static/css',
  jsSrcPath: './src/js/**/*.js',
  jsDistDir: './public/static/js',
};


function clean(done) {
  del([paths.cssDistDir, paths.jsDistDir]);
  done();
}

function css(done, file) {

  const entries = (file === undefined) ? paths.scssSrcPath : [file];

  return src(entries)
    .pipe(sourcemaps.init())
      .pipe(sass({
        outputStyle: 'compressed',
        includePaths: [paths.boostrapSassDir]
      }))
      .pipe(rename({
        suffix: '.min'
      }))
    .pipe(sourcemaps.write('maps', {
      includeContent: true,
      sourceRoot: paths.scssSrcPath
    }))
    .pipe(dest(paths.cssDistDir))
    .pipe(livereload());
}

// Adapted from https://github.com/MaheshSasidharan/gulp-babel-browserify/blob/master/gulpfile.js
function js(done, file) {

  const entries = (file === undefined) ? glob.sync(paths.jsSrcPath) : [file];

  entries.forEach((entry) => {
    let fileName = entry.split('/').pop(),
        bundleName = fileName.replace(/\.js$/, '.min.js');

    const bundler = browserify({entries: entry}, { debug: true })
          .transform(babel.configure({
            presets: ["@babel/preset-env"]
          }));

    bundler.bundle()
      .on("error", function (err) { console.error(err); this.emit("end"); })
      .pipe(source(bundleName))
      .pipe(buffer())
      .pipe(sourcemaps.init({ loadMaps: true }))
        .pipe(uglify())
      .pipe(sourcemaps.write('maps'))
      .pipe(dest(paths.jsDistDir))
      .pipe(livereload());

  });

  done();

}

function watch(done) {

  livereload.listen({start: true});

  gulpWatch(paths.scssSrcPath)
    .on('change', (file) => {
      return css(done, file)
    });

  gulpWatch(paths.jsSrcPath)
    .on('change', (file) => {
      return js(done, file)
    });

  done();

}

exports.clean = clean;
exports.css = css;
exports.js = js;
exports.watch = watch;
exports.build = series(clean, parallel(css, js));
exports.default = series(clean, css, js, watch);
