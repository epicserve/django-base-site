// const webpack = require( 'webpack' );
const path = require('path'),
      {CleanWebpackPlugin} = require('clean-webpack-plugin'),
      glob = require('glob'),
      LiveReloadPlugin = require('webpack-livereload-plugin'),
      MiniCssExtractPlugin = require('mini-css-extract-plugin'),
      StylelintPlugin = require('stylelint-webpack-plugin'),
      isDevMode = process.env.NODE_ENV === 'development';

const paths = {
  sassFiles: glob.sync('./src/scss/**/*.scss'),
  jsFiles: glob.sync('./src/js/**/*.js'),
  outputDir: path.join(__dirname, 'public/static/dist/'),
};

function getEntries() {
  let entries = {};

  paths.sassFiles.forEach((srcFile) => {
    let dstFile = srcFile.replace(/^\.\/src\/scss/, '/css').replace(/\.scss$/, '.min'),
        fileName = srcFile.split('/').pop();

    if (/^_/.test(fileName) === false) {
      entries[dstFile] = srcFile;
    }

  });

  paths.jsFiles.forEach((srcFile) => {
    let dstFile = srcFile.replace(/^\.\/src/, '').replace('.js', '.min.js');
    entries[dstFile] = srcFile;
  });

  return entries;
}

module.exports = {
  context: __dirname,
  mode: isDevMode ? 'development' : 'production',
  entry: getEntries,
  output: {
    path: paths.outputDir,
    filename: '[name]',
  },
  module: {
    rules: [
      {
        enforce: 'pre',
        test: /\.(vue|js)$/,
        exclude: /node_modules/,
        loader: 'eslint-loader',
        options: {
          failOnError: true,
        },
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
      },
      {
        test: /\.(s)?css$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              hmr: isDevMode,
            },
          },
          {
            loader: 'css-loader',
            options: {
              url: false,
            },
          },
          'sass-loader',
        ],
      },
    ],
  },
  plugins: [
    new CleanWebpackPlugin({
      cleanOnceBeforeBuildPatterns: ['css/', 'js/'],
      cleanAfterEveryBuildPatterns: ['css/**/*.min'],
    }),
    new LiveReloadPlugin(),
    new MiniCssExtractPlugin({
      // Options similar to the same options in webpackOptions.output
      // all options are optional
      filename: '[name].css',
      chunkFilename: '[id].css',
      ignoreOrder: false, // Enable to remove warnings about conflicting order
    }),
    new StylelintPlugin({
      context: 'src/scss',
      fix: true,
    }),
  ],
  // Necessary for file changes inside docker node volume to get picked up
  watchOptions: {
    aggregateTimeout: 300,
    poll: 1000,
  },
  resolve: {
    alias: {
      vue: isDevMode ? 'vue/dist/vue.js' : 'vue/dist/vue.min.js',
    },
    extensions: ['.js'],
  },
};
