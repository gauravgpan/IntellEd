/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  workflowSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Workflow Diagrams',
      items: [
        'workflows/platform-tutorial',
        'workflows/tutor-feedback',
        'workflows/hybrid',
      ],
    },
    'comparison',
  ],
};

module.exports = sidebars;
