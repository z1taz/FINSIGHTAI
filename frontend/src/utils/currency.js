export const CURRENCIES = [
  { code: 'INR', symbol: '₹', rate: 83.0, label: 'INR (₹)' },
  { code: 'USD', symbol: '$', rate: 1.0, label: 'USD ($)' },
  { code: 'EUR', symbol: '€', rate: 0.92, label: 'EUR (€)' },
  { code: 'GBP', symbol: '£', rate: 0.78, label: 'GBP (£)' },
];

export function formatCurrency(amount, currencyCode = 'INR') {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '0.00';
  }
  
  const currencyObj = CURRENCIES.find(c => c.code === currencyCode) || CURRENCIES[0];
  const converted = amount * currencyObj.rate;
  
  // Format with commas and appropriate decimal places
  const formattedNumber = new Intl.NumberFormat(
    currencyCode === 'INR' ? 'en-IN' : 'en-US',
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }
  ).format(converted);

  return `${currencyObj.symbol}${formattedNumber}`;
}
