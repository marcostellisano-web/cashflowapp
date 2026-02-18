import { cn } from '../../lib/utils';

interface Step {
  label: string;
  description: string;
}

const STEPS: Step[] = [
  { label: 'Upload', description: 'Upload budget file' },
  { label: 'Schedule', description: 'Production parameters' },
  { label: 'Distribution', description: 'Configure spend curves' },
  { label: 'Output', description: 'Preview & download' },
];

interface AppShellProps {
  currentStep: number;
  onHome: () => void;
  children: React.ReactNode;
}

export default function AppShell({ currentStep, onHome, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          {/* Logo — click to return home */}
          <button
            onClick={onHome}
            className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg"
            aria-label="Return to home"
          >
            <img
              src="/logo.png"
              alt="Production Finance Engine"
              className="h-16 w-auto object-contain"
            />
          </button>

          {/* Tagline */}
          <p className="hidden sm:block text-sm text-gray-400 font-light tracking-wide">
            comprehensive budget analysis.{' '}
            <span className="text-blue-600 font-medium">made simple.</span>
          </p>
        </div>
      </header>

      {/* Stepper */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <ol className="flex items-center gap-2">
            {STEPS.map((step, idx) => (
              <li key={step.label} className="flex items-center gap-2">
                <div
                  className={cn(
                    'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium',
                    idx === currentStep && 'bg-blue-600 text-white',
                    idx < currentStep && 'bg-green-100 text-green-700',
                    idx > currentStep && 'bg-gray-100 text-gray-400',
                  )}
                >
                  <span
                    className={cn(
                      'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                      idx === currentStep && 'bg-blue-500 text-white',
                      idx < currentStep && 'bg-green-500 text-white',
                      idx > currentStep && 'bg-gray-300 text-gray-500',
                    )}
                  >
                    {idx < currentStep ? '\u2713' : idx + 1}
                  </span>
                  <span className="hidden sm:inline">{step.label}</span>
                </div>
                {idx < STEPS.length - 1 && (
                  <div className="w-8 h-px bg-gray-300" />
                )}
              </li>
            ))}
          </ol>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
