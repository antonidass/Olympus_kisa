import { Composition } from "remotion";
import { Intro } from "./Intro";
import {
  IcarusVideo,
  calculateIcarusMetadata,
  icarusDefaultProps,
} from "./IcarusVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Intro"
        component={Intro}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="IcarusAndDaedalus"
        component={IcarusVideo}
        calculateMetadata={calculateIcarusMetadata}
        defaultProps={icarusDefaultProps}
        durationInFrames={1800}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
