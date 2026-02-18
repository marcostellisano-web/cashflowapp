import { BadgeCheck, FileOutput, Gauge, Workflow } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Step {
  label: string;
  description: string;
}

const STEPS: Step[] = [
  { label: 'Upload', description: 'Upload budget file' },
  { label: 'Schedule', description: 'Production parameters' },
  { label: 'Distribution', description: 'Configure spend curves' },
  { label: 'Output', description: 'Preview & export' },
];

interface AppShellProps {
  currentStep: number;
  children: React.ReactNode;
}

const quickStats = [
  {
    icon: BadgeCheck,
    title: 'Budget Validation',
    description: 'Upload and validate structured line items.',
  },
  {
    icon: Workflow,
    title: 'Curve Allocation',
    description: 'Assign curve logic by production phase.',
  },
  {
    icon: FileOutput,
    title: 'Multi-format Export',
    description: 'Export budget and cashflow outputs instantly.',
  },
  {
    icon: Gauge,
    title: 'Preview Dashboard',
    description: 'Review totals before downloading deliverables.',
  },
];

export default function AppShell({ currentStep, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <img
              src="/pfe-logo.svg"
              alt="Production Finance Engine logo"
              className="h-11 w-11 rounded-lg object-cover"
            />
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Production Finance Engine</p>
              <h1 className="text-lg font-semibold sm:text-xl">Cashflow & Budget Workspace</h1>
            </div>
          </div>
          <div className="hidden rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-medium text-green-700 sm:block">
            Live planning mode
          </div>
        </div>

        <div className="mx-auto w-full max-w-7xl px-6 pb-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {quickStats.map(({ icon: Icon, title, description }) => (
              <div key={title} className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
                <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-gray-800">
                  <Icon className="h-4 w-4 text-blue-600" />
                  {title}
                </div>
                <p className="text-xs text-gray-500">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </header>

      <nav className="border-b border-gray-200 bg-white px-6 py-3">
        <ol className="mx-auto flex w-full max-w-7xl items-center gap-2 overflow-x-auto">
          {STEPS.map((step, idx) => (
            <li key={step.label} className="flex items-center gap-2">
              <div
                className={cn(
                  'flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium',
                  idx === currentStep && 'bg-blue-600 text-white',
                  idx < currentStep && 'bg-green-100 text-green-700',
                  idx > currentStep && 'bg-gray-100 text-gray-400',
                )}
              >
                <span
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold',
                    idx === currentStep && 'bg-blue-500 text-white',
                    idx < currentStep && 'bg-green-500 text-white',
                    idx > currentStep && 'bg-gray-300 text-gray-500',
                  )}
                >
                  {idx < currentStep ? '\u2713' : idx + 1}
                </span>
                <span>{step.label}</span>
              </div>
              <span className="hidden text-xs text-gray-400 lg:inline">{step.description}</span>
              {idx < STEPS.length - 1 && (
                <div className="h-px w-8 bg-gray-300" />
              )}
            </li>
          ))}
        </ol>
      </nav>

      <main className="mx-auto w-full max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
