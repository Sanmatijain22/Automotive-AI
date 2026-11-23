import React, { useState } from 'react';
import { 
  CheckCircle2, 
  ArrowRight, 
  Flame, 
  ShieldAlert, 
  Wrench, 
  FileDown, 
  Play, 
  RotateCcw,
  Sparkles
} from 'lucide-react';
import { triggerSimulationScenario, resetSimulation, getReportDownloadUrl } from '../services/api';

interface DemoScenarioGuideProps {
  onSelectMachine: (id: string) => void;
  onNavigateTab: (tab: string) => void;
  onRefresh: () => void;
}

export const DemoScenarioGuide: React.FC<DemoScenarioGuideProps> = ({
  onSelectMachine,
  onNavigateTab,
  onRefresh
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isBusy, setIsBusy] = useState(false);

  const steps = [
    {
      num: 1,
      title: 'Nominal Baseline',
      desc: 'VH-001 operating normally with healthy engine temperature and low vibration.',
      actionLabel: 'Set Baseline',
      run: async () => {
        setIsBusy(true);
        await resetSimulation();
        onSelectMachine('VH-001');
        onNavigateTab('machines');
        onRefresh();
        setIsBusy(false);
        setCurrentStep(2);
      }
    },
    {
      num: 2,
      title: 'Inject Engine Thermal Stress',
      desc: 'Increase engine temperature and drivetrain vibration on VH-001.',
      actionLabel: 'Inject Fault',
      run: async () => {
        setIsBusy(true);
        await triggerSimulationScenario('FAULT_INJECTION', 'VH-001', 'engine_overheat');
        onSelectMachine('VH-001');
        onNavigateTab('machines');
        onRefresh();
        setIsBusy(false);
        setCurrentStep(3);
      }
    },
    {
      num: 3,
      title: 'AI Anomaly & Risk Evaluation',
      desc: 'Observe Isolation Forest and Random Forest classify VH-001 as High Risk with contributing factors.',
      actionLabel: 'View AI Intelligence',
      run: async () => {
        onNavigateTab('predictions');
        setCurrentStep(4);
      }
    },
    {
      num: 4,
      title: 'Review Predictive Alerts',
      desc: 'Automated alert for VH-001: critical engine temperature or drivetrain vibration exceedance.',
      actionLabel: 'Go to Alerts',
      run: async () => {
        onNavigateTab('alerts');
        setCurrentStep(5);
      }
    },
    {
      num: 5,
      title: 'Prescribed Recommendations',
      desc: 'Actionable guidance: cooling-system inspection and drivetrain vibration diagnosis.',
      actionLabel: 'View Work Orders',
      run: async () => {
        onNavigateTab('maintenance');
        setCurrentStep(6);
      }
    },
    {
      num: 6,
      title: 'Generate PDF Report',
      desc: 'Download the vehicle health PDF report with telemetry and AI diagnostics.',
      actionLabel: 'Download VH-001 PDF',
      run: async () => {
        window.open(getReportDownloadUrl('VH-001'), '_blank');
        onNavigateTab('reports');
        setCurrentStep(1);
      }
    }
  ];

  const current = steps[currentStep - 1];

  return (
    <div className="bg-gradient-to-r from-slate-900 via-blue-950/60 to-slate-900 border-b border-blue-900/40 px-4 py-2.5 text-xs">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Title */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="p-1 rounded bg-blue-600/30 border border-blue-500/50 text-blue-400">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="font-bold text-white flex items-center gap-1.5">
              <span>Interactive Demonstration Walkthrough</span>
              <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.2 rounded border border-blue-400/30">
                Step {currentStep} of 6
              </span>
            </div>
            <p className="text-[11px] text-slate-300">
              <strong className="text-blue-300">{current.title}:</strong> {current.desc}
            </p>
          </div>
        </div>

        {/* Step Progression Buttons */}
        <div className="flex items-center flex-wrap gap-1.5">
          {steps.map((s) => (
            <button
              key={s.num}
              onClick={() => setCurrentStep(s.num)}
              className={`h-6 px-2 rounded font-mono text-[11px] font-bold transition-all ${
                currentStep === s.num
                  ? 'bg-blue-600 text-white shadow-sm ring-1 ring-blue-400'
                  : currentStep > s.num
                  ? 'bg-slate-800 text-emerald-400 hover:bg-slate-700'
                  : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800'
              }`}
            >
              {currentStep > s.num ? `✓ S${s.num}` : `S${s.num}`}
            </button>
          ))}

          {/* Action Trigger */}
          <button
            onClick={current.run}
            disabled={isBusy}
            className="flex items-center gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-3 py-1 rounded font-bold shadow-md shadow-blue-700/30 transition-all text-xs"
          >
            <span>{current.actionLabel}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
