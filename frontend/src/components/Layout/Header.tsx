export type PageType = 'ppa' | 'workload' | 'yield' | 'history';

interface HeaderProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

export function Header({ currentPage, onPageChange }: HeaderProps) {
  const navItems: { id: PageType; label: string }[] = [
    { id: 'ppa', label: 'PPA Optimizer' },
    { id: 'workload', label: 'Workload Analyzer' },
    { id: 'yield', label: 'Yield Dashboard' },
    { id: 'history', label: 'History' },
  ];

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-nexus-500 to-nexus-700 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">HySpace</h1>
              <p className="text-xs text-gray-500">AI Chip Design Platform</p>
            </div>
          </div>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  currentPage === item.id
                    ? 'bg-nexus-100 text-nexus-700'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
