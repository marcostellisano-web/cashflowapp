interface HomePageProps {
  onSelectCashflow: () => void;
}

export default function HomePage({ onSelectCashflow }: HomePageProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero / Banner */}
      <div className="bg-gradient-to-br from-white to-blue-50 border-b border-gray-200 h-56 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          {/* Logo */}
          <img
            src="/logo.png"
            alt="Production Finance Engine"
            className="h-[432px] w-auto object-contain flex-shrink-0 -ml-[144px]"
          />

          {/* Headline */}
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 leading-tight text-right">
            Production finance
            <span className="text-blue-600"> — automated.</span>
          </h1>
        </div>
      </div>

      {/* Tool Selection */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <p className="text-base text-gray-500 leading-relaxed mb-10">
          Upload your Movie Magic budget and instantly generate a modeled
          cashflow and tax credit forecast.
        </p>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-8">
          What would you like to generate?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cashflow Card — active */}
          <button
            onClick={onSelectCashflow}
            className="group text-left bg-white border border-gray-200 rounded-2xl p-8 shadow-sm hover:shadow-md hover:border-blue-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <div className="flex items-start justify-between mb-6">
              {/* Icon */}
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.75}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              {/* Arrow */}
              <svg
                className="w-5 h-5 text-gray-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>

            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Production Cashflow
            </h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              Generate a week-by-week cashflow forecast from your production
              budget. Assign spend curves and phase distributions across prep,
              shoot, wrap, and post.
            </p>

            <div className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 group-hover:text-blue-700">
              Get started
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </div>
          </button>

          {/* Tax Credit Filing Budget Card — coming soon */}
          <div className="relative text-left bg-white border border-gray-100 rounded-2xl p-8 shadow-sm opacity-60 cursor-not-allowed">
            {/* Coming Soon Badge */}
            <span className="absolute top-4 right-4 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
              Coming soon
            </span>

            <div className="flex items-start justify-between mb-6">
              <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.75}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
            </div>

            <h3 className="text-xl font-semibold text-gray-500 mb-2">
              Tax Credit Filing Budget
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Produce a structured budget output formatted for tax credit
              applications. Automatically categorise expenditure against
              eligible spend criteria.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
