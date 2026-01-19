import { Button } from '@/components/livekit/button';

function WelcomeImage() {
  return (
    <img
      src="/Jarvis.gif"
      alt="Jarvis"
      className="
        mb-10
        w-full
        max-w-[900px]
        h-auto
        mx-auto
        drop-shadow-[0_0_80px_rgba(0,180,255,0.45)]
      "
    />
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center min-h-screen">
        <WelcomeImage />

        <p className="text-foreground max-w-prose pt-1 leading-6 font-medium">
          Chat live with Jarvis
        </p>

        <Button
          variant="primary"
          size="lg"
          onClick={onStartCall}
          className="mt-6 w-64 font-mono"
        >
          {startButtonText}
        </Button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal md:text-sm">
          Need help getting set up? Check our Channel{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://www.youtube.com/@Code_x_Play"
            className="underline"
          >
            Code x Play
          </a>
          .
        </p>
      </div>
    </div>
  );
};
