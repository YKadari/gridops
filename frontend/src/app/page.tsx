type Forecast = {
  horizon_hours: number;
  issue_at: string;
  target_at: string;
  predicted_demand: number;
  units: string;
  eia_latest_observed_at: string;
};

async function getForecast(
  horizon: 24 | 48
): Promise<Forecast> {
  const baseUrl = process.env.GRIDOPS_API_URL;

  if (!baseUrl) {
    throw new Error(
      "GRIDOPS_API_URL is not configured"
    );
  }

  const response = await fetch(
    `${baseUrl}/forecasts/latest/${horizon}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load ${horizon}h forecast`
    );
  }

  return response.json();
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value: string) {
  return new Date(value).toLocaleString(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  );
}

function ForecastCard({
  forecast,
}: {
  forecast: Forecast;
}) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
      <p className="text-sm text-slate-400">
        {forecast.horizon_hours} Hour Forecast
      </p>

      <p className="mt-3 text-3xl font-semibold text-white">
        {formatNumber(
          forecast.predicted_demand
        )}{" "}
        <span className="text-base font-normal text-slate-400">
          MWh
        </span>
      </p>

      <div className="mt-6">
        <p className="text-sm text-slate-400">
          Target
        </p>

        <p className="mt-1 text-sm text-white">
          {formatDate(
            forecast.target_at
          )}
        </p>
      </div>
    </div>
  );
}

export default async function Home() {
  const [forecast24, forecast48] =
    await Promise.all([
      getForecast(24),
      getForecast(48),
    ]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-4xl px-6 py-14">
        <header className="mb-12">
          <h1 className="text-4xl font-bold">
            GridOps
           </h1>
            <h2 className="text-4xl font-bold">
                By: Yashwanth Kadari
            </h2>

          <p className="mt-2 text-lg text-slate-400">
            PJM Electricity Demand Forecasting
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          <ForecastCard
            forecast={forecast24}
          />

          <ForecastCard
            forecast={forecast48}
          />
        </div>

        <div className="mt-10 border-t border-slate-800 pt-6 text-sm text-slate-400">
          <p>
            Latest PJM data:{" "}
            <span className="text-slate-300">
              {formatDate(
                forecast24.eia_latest_observed_at
              )}
            </span>
          </p>

          <p className="mt-2">
            System status:{" "}
            <span className="text-green-400">
              Online
            </span>
          </p>

          <p className="mt-2">
            PJM data updates hourly at :05
            {" • "}
            Forecasts refresh hourly at :15
          </p>
        </div>
      </div>
    </main>
  );
}