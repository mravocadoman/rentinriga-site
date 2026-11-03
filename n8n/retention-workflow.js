// Source of the n8n workflow "Rent in Riga — delete leads after 12 months" (tuTr2xL1aH7kEtOx).
// Keeps the privacy notice's 12-month retention promise. Successful runs are not saved
// (saveDataSuccessExecution: none) so execution logs never keep copies of deleted leads.
import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';

const daily = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.4,
  config: {
    name: 'Daily 03:15',
    parameters: { rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 3, triggerAtMinute: 15 }] } },
  },
});

const cutoff = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Cutoff',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `// Privacy notice (rentinrigalatvia.lv/privacy/): leads are kept 12 months after we receive them.
const now = new Date();
const cutoff = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
// Guard: never delete anything younger than 360 days, whatever happens to the date maths above.
if (now - cutoff < 360 * 864e5) throw new Error('cutoff too recent: ' + cutoff.toISOString());
return [{ json: { cutoff: cutoff.toISOString() } }];`,
    },
  },
});

const purge = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Delete leads older than 12 months',
    executeOnce: true,
    parameters: {
      resource: 'row',
      operation: 'deleteRows',
      dataTableId: { __rl: true, mode: 'id', value: 'IfphWRSOm2SkfFaD', cachedResultName: 'Rent in Riga leads' },
      matchType: 'allConditions',
      filters: { conditions: [{ keyName: 'createdAt', condition: 'lt', keyValue: expr('{{ $json.cutoff }}') }] },
      options: { dryRun: false },
    },
  },
});

export default workflow('rentinriga-retention', 'Rent in Riga — delete leads after 12 months', {
  settings: { executionOrder: 'v1', errorWorkflow: 'R9OmXjBXdhYetZkM', timezone: 'Europe/Riga', saveDataSuccessExecution: 'none' },
})
  .add(daily)
  .to(cutoff)
  .to(purge);
