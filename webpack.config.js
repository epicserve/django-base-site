// const webpack = require( 'webpack' );
const path = require('path'),
      {CleanWebpackPlugin} = require('clean-webpack-plugin'),
      LiveReloadPlugin = require('webpack-livereload-plugin'),
      MiniCssExtractPlugin = require('mini-css-extract-plugin'),
      isDevMode = process.env.NODE_ENV === 'development';

module.exports = {
  context: __dirname,
  mode: isDevMode ? 'development' : 'production',
  entry: {
    '/js/base.min.js': './src/js/base.js',
    '/css/base.min': './src/scss/base.scss',
  },
  output: {
    path: path.join(__dirname, 'public/static/dist/'),
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
