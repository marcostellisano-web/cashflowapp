import { type ReactNode, useEffect, useMemo, useState } from 'react';
import type { ParsedBudget } from '../../types/budget';
import type { BreakoutOverride } from '../../types/tax_credit';

interface Props {
  budget: ParsedBudget;
  overrides: BreakoutOverride[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

function pct(n: number): string {
  return (n * 100).toFixed(1) + '%';
}

/** Calculate Ontario Labour and Fed Labour from overrides × budget line items */
function calcLabourFromOverrides(
  budget: ParsedBudget,
  overrides: BreakoutOverride[],
): { ontarioLabour: number; fedLabour: number } {
  const overrideMap = new Map(overrides.map((o) => [o.account_code, o]));
  let ontarioLabour = 0;
  let fedLabour = 0;
  for (const item of budget.line_items) {
    const ov = overrideMap.get(item.code);
    if (ov) {
      ontarioLabour += item.total * (ov.prov_labour_pct ?? 0);
      fedLabour += item.total * (ov.fed_labour_pct ?? 0);
    }
  }
  return { ontarioLabour, fedLabour };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionHeader({ label }: { label: string }) {
  return (
    <tr>
      <td
        colSpan={3}
        className="bg-gray-900 text-white font-bold text-xs px-3 py-2 uppercase tracking-wide"
      >
        {label}
      </td>
    </tr>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <tr>
      <td colSpan={3} className="pt-3 pb-1 px-3 font-bold text-sm text-gray-700">
        {label}
      </td>
    </tr>
  );
}

function Spacer() {
  return (
    <tr>
      <td colSpan={3} className="h-2" />
    </tr>
  );
}

function Row({
  label,
  mid,
  value,
  bold,
  indent,
  valueNeg,
}: {
  label: string;
  mid?: ReactNode;
  value?: ReactNode;
  bold?: boolean;
  indent?: boolean;
  valueNeg?: boolean;
}) {
  return (
    <tr className={bold ? 'bg-gray-50' : ''}>
      <td
        className={`px-3 py-1.5 text-sm ${indent ? 'pl-8' : ''} ${bold ? 'font-semibold text-gray-900' : 'text-gray-700'}`}
      >
        {label}
      </td>
      <td className="px-3 py-1.5 text-sm text-gray-600 text-center w-28">{mid}</td>
      <td
        className={`px-3 py-1.5 text-sm text-right w-36 font-mono ${bold ? 'font-semibold' : ''} ${valueNeg ? 'text-gray-700' : 'text-gray-900'}`}
      >
        {value}
      </td>
    </tr>
  );
}

function InputRow({
  label,
  value,
  onChange,
  placeholder,
  indent,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  indent?: boolean;
}) {
  return (
    <tr>
      <td className={`px-3 py-1 text-sm text-gray-700 ${indent ? 'pl-8' : ''}`}>{label}</td>
      <td className="px-3 py-1 text-sm text-center w-28" />
      <td className="px-3 py-1 w-36">
        <input
          type="text"
          inputMode="numeric"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder ?? '0'}
          className="w-full text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </td>
    </tr>
  );
}

function TotalRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <tr className={highlight ? 'bg-gray-900' : 'bg-gray-100'}>
      <td
        colSpan={2}
        className={`px-3 py-2 text-sm font-bold ${highlight ? 'text-white' : 'text-gray-900'}`}
      >
        {label}
      </td>
      <td
        className={`px-3 py-2 text-sm font-bold text-right font-mono ${highlight ? 'text-white' : 'text-gray-900'}`}
      >
        {value}
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function OntarioTaxCreditTab({ budget, overrides }: Props) {
  const totalProductionCost = budget.total_budget;

  // Seed from overrides when they load
  const { ontarioLabour: calcOntarioLabour, fedLabour: calcFedLabour } = useMemo(
    () => calcLabourFromOverrides(budget, overrides),
    [budget, overrides],
  );

  // Ontario Provincial section inputs
  const [ontarioLabourInput, setOntarioLabourInput] = useState('');
  const [equityInput, setEquityInput] = useState('');
  const [deferralsInput, setDeferralsInput] = useState('');
  const [othersInput, setOthersInput] = useState('');
  const [regionalBonus, setRegionalBonus] = useState(false);

  // Federal section inputs
  const [fedDeferralsInput, setFedDeferralsInput] = useState('');
  const [meInput, setMeInput] = useState('');
  const [assistanceInput, setAssistanceInput] = useState('');
  const [labourExpInput, setLabourExpInput] = useState('');
  const [labourDeferralsInput, setLabourDeferralsInput] = useState('');
  const [ownershipPctInput, setOwnershipPctInput] = useState('100');

  // When overrides change, seed the labour fields if not yet edited
  const [seededLabour, setSeededLabour] = useState(false);
  useEffect(() => {
    if (!seededLabour && overrides.length > 0) {
      if (calcOntarioLabour > 0) setOntarioLabourInput(String(Math.round(calcOntarioLabour)));
      if (calcFedLabour > 0) setLabourExpInput(String(Math.round(calcFedLabour)));
      setSeededLabour(true);
    }
  }, [overrides, calcOntarioLabour, calcFedLabour, seededLabour]);

  // -------------------------------------------------------------------------
  // Parse helpers
  // -------------------------------------------------------------------------
  const parseNum = (s: string): number => {
    const n = parseFloat(s.replace(/,/g, ''));
    return isNaN(n) ? 0 : n;
  };

  const ontarioLabour = parseNum(ontarioLabourInput);
  const equity = parseNum(equityInput);
  const deferrals = parseNum(deferralsInput);
  const others = parseNum(othersInput);
  const fedDeferrals = parseNum(fedDeferralsInput);
  const meAmount = parseNum(meInput);
  const assistance = parseNum(assistanceInput);
  const labourExp = parseNum(labourExpInput);
  const labourDeferrals = parseNum(labourDeferralsInput);
  const ownershipPct = parseNum(ownershipPctInput);

  // -------------------------------------------------------------------------
  // ONTARIO PROVINCIAL TAX CREDIT
  // -------------------------------------------------------------------------
  const proportionOfLabour = totalProductionCost > 0 ? ontarioLabour / totalProductionCost : 0;

  // Section B
  const totalReductions = equity + deferrals + others;
  const netProductionCost = ontarioLabour - totalReductions;

  // Section C
  const generalOFTTC = netProductionCost * 0.35;
  const regionalBonusAmount = regionalBonus ? netProductionCost * 0.1 : 0;
  const totalOFTTC = generalOFTTC + regionalBonusAmount;
  const pctBudgetOFTTC = totalProductionCost > 0 ? totalOFTTC / totalProductionCost : 0;

  // -------------------------------------------------------------------------
  // FEDERAL TAX CREDIT
  // -------------------------------------------------------------------------
  const meDeduction = meAmount * 0.5;
  const netProductionCostFed =
    totalProductionCost - totalOFTTC - fedDeferrals - meDeduction - assistance;
  const eligibleCostA = netProductionCostFed * 0.6;

  const labourSubtotal = labourExp - labourDeferrals;
  const netLabourB = labourSubtotal * (ownershipPct / 100);
  const eligibleCostFed = Math.min(eligibleCostA, netLabourB);
  const totalFedCredit = eligibleCostFed * 0.25;
  const pctBudgetFed = totalProductionCost > 0 ? totalFedCredit / totalProductionCost : 0;

  // -------------------------------------------------------------------------
  // Summary
  // -------------------------------------------------------------------------
  const totalTaxCredit = totalOFTTC + totalFedCredit;
  const pctTotalCredits = totalProductionCost > 0 ? totalTaxCredit / totalProductionCost : 0;

  return (
    <div className="space-y-4">
      {/* Info banner */}
      {overrides.length > 0 && (
        <div className="flex items-start gap-2 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
          <svg className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-blue-700">
            Ontario Labour and Federal Labour Expenditure have been estimated from your Breakout
            Overrides. Adjust them in the fields below if needed.
          </p>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {/* Title block */}
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
            ONTARIO — FULL (OFTTC)
          </p>
          <p className="text-sm font-semibold text-gray-800 mt-0.5">Tax Credit Calculation</p>
        </div>

        <table className="w-full border-collapse">
          <colgroup>
            <col className="w-full" />
            <col className="w-28" />
            <col className="w-36" />
          </colgroup>
          <tbody>
            {/* ============================================================ */}
            {/* ONTARIO PROVINCIAL TAX CREDIT */}
            {/* ============================================================ */}
            <SectionHeader label="Ontario Provincial Tax Credit" />
            <SectionLabel label="A" />

            <Row label="Total Production Cost" value={fmt(totalProductionCost)} bold />
            <InputRow
              label="Estimate of Total Ont. Labour"
              value={ontarioLabourInput}
              onChange={setOntarioLabourInput}
            />
            <Row
              label="Proportion of labour"
              value={pct(proportionOfLabour)}
            />

            <Spacer />
            <SectionLabel label="B" />

            <Row label="Estimate of total Labour expenditure" value={fmt(ontarioLabour)} />
            <tr>
              <td className="px-3 py-1 text-sm text-gray-700">Reduction</td>
              <td className="px-3 py-1 text-sm text-gray-500 text-center">Equity</td>
              <td className="px-3 py-1 w-36">
                <input
                  type="text"
                  inputMode="numeric"
                  value={equityInput}
                  onChange={(e) => setEquityInput(e.target.value)}
                  placeholder="0"
                  className="w-full text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
            </tr>
            <tr>
              <td className="px-3 py-1 text-sm text-gray-700" />
              <td className="px-3 py-1 text-sm text-gray-500 text-center">Deferrals</td>
              <td className="px-3 py-1 w-36">
                <input
                  type="text"
                  inputMode="numeric"
                  value={deferralsInput}
                  onChange={(e) => setDeferralsInput(e.target.value)}
                  placeholder="0"
                  className="w-full text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
            </tr>
            <tr>
              <td className="px-3 py-1 text-sm text-gray-700" />
              <td className="px-3 py-1 text-sm text-gray-500 text-center">Others</td>
              <td className="px-3 py-1 w-36">
                <input
                  type="text"
                  inputMode="numeric"
                  value={othersInput}
                  onChange={(e) => setOthersInput(e.target.value)}
                  placeholder="0"
                  className="w-full text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
            </tr>
            <Row label="Net Production cost" value={fmt(netProductionCost)} bold />

            <Spacer />
            <SectionLabel label="C" />

            <Row label="Ontario Labour" value={fmt(netProductionCost)} />
            <Row label="General OFTTC (×35%)" value={fmt(generalOFTTC)} bold />

            {/* Regional bonus row with toggle */}
            <tr>
              <td className="px-3 py-1.5 text-sm text-gray-700">Regional Bonus – 10%</td>
              <td className="px-3 py-1.5 text-center">
                <button
                  onClick={() => setRegionalBonus((v) => !v)}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold transition-colors ${
                    regionalBonus
                      ? 'bg-green-100 text-green-700 border border-green-300'
                      : 'bg-gray-100 text-gray-500 border border-gray-300'
                  }`}
                >
                  {regionalBonus ? 'y' : 'n'}
                </button>
              </td>
              <td className="px-3 py-1.5 text-sm text-right font-mono font-semibold text-gray-900">
                {regionalBonus ? fmt(regionalBonusAmount) : '—'}
              </td>
            </tr>

            <Spacer />
            <TotalRow label="TOTAL OFTTC" value={fmt(totalOFTTC)} />
            <Row label="Percentage of budget" value={pct(pctBudgetOFTTC)} />
            <Spacer />

            {/* ============================================================ */}
            {/* FEDERAL TAX CREDIT */}
            {/* ============================================================ */}
            <SectionHeader label="Federal Tax Credit" />
            <Spacer />

            <Row label="Total Production cost" value={fmt(totalProductionCost)} bold />
            <Spacer />
            <Row label="ON Tax Credits" value={`(${fmt(totalOFTTC)})`} valueNeg />
            <InputRow
              label="Deferrals"
              value={fedDeferralsInput}
              onChange={setFedDeferralsInput}
            />

            {/* 50% Meals & Entertainment */}
            <tr>
              <td className="px-3 py-1.5 text-sm text-gray-700">50% Meals &amp; Entertainment</td>
              <td className="px-3 py-1.5 w-28">
                <input
                  type="text"
                  inputMode="numeric"
                  value={meInput}
                  onChange={(e) => setMeInput(e.target.value)}
                  placeholder="0"
                  className="w-full text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </td>
              <td className="px-3 py-1.5 text-sm text-right font-mono text-gray-700">
                {meAmount > 0 ? `(${fmt(meDeduction)})` : '—'}
              </td>
            </tr>

            <InputRow label="Assistance" value={assistanceInput} onChange={setAssistanceInput} />
            <Row label="Net Production Cost" value={fmt(netProductionCostFed)} bold />
            <Row label="(A) Eligible production cost" value={fmt(eligibleCostA)} bold indent />
            <Spacer />

            <InputRow
              label="Labour expenditure"
              value={labourExpInput}
              onChange={setLabourExpInput}
            />
            <Spacer />
            <InputRow
              label="Deferrals"
              value={labourDeferralsInput}
              onChange={setLabourDeferralsInput}
              indent
            />
            <Row label="Sub-total" value={fmt(labourSubtotal)} />

            {/* Ownership % */}
            <tr>
              <td className="px-3 py-1.5 text-sm text-gray-700">Percentage of ownership</td>
              <td className="px-3 py-1.5 w-28" />
              <td className="px-3 py-1.5 w-36">
                <div className="flex items-center justify-end gap-1">
                  <input
                    type="text"
                    inputMode="numeric"
                    value={ownershipPctInput}
                    onChange={(e) => setOwnershipPctInput(e.target.value)}
                    placeholder="100"
                    className="w-20 text-right font-mono text-sm px-2 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-500">%</span>
                </div>
              </td>
            </tr>

            <Row label="(B) Net labour expenditure" value={fmt(netLabourB)} bold />
            <Spacer />
            <Row label="Eligible cost for Fed. Tax Credit" value={fmt(eligibleCostFed)} bold />
            <Spacer />
            <Row label="Total Federal Tax Credit" value={fmt(totalFedCredit)} bold />
            <Row label="Percentage of budget" value={pct(pctBudgetFed)} />

            <Spacer />
            <TotalRow label="TOTAL TAX CREDIT" value={`${fmt(totalTaxCredit)} $`} highlight />

            {/* Summary footer */}
            <Spacer />
            <Row label="Total Production Cost" value={fmt(totalProductionCost)} bold />
            <Row
              label="Percentage of Total Tax Credits"
              value={pct(pctTotalCredits)}
              bold
            />
            <Spacer />
          </tbody>
        </table>
      </div>
    </div>
  );
}
