/**
 * Module Federation — o shell carrega cada MFE em runtime a partir do seu
 * próprio deploy. Ver apps/README.md para a lista de remotes.
 */
const { withModuleFederationPlugin, shareAll } = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({
  remotes: {
    'customer-mfe': 'customer_mfe@http://localhost:4201/remoteEntry.js',
    'analytics-mfe': 'analytics_mfe@http://localhost:4202/remoteEntry.js',
    'ai-operations-mfe': 'ai_operations_mfe@http://localhost:4203/remoteEntry.js',
    'governance-mfe': 'governance_mfe@http://localhost:4204/remoteEntry.js',
  },
  shared: {
    ...shareAll({ singleton: true, strictVersion: true, requiredVersion: 'auto' }),
  },
});
