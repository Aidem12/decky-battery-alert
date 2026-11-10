import {
  PanelSection,
  PanelSectionRow,
  staticClasses,
} from "@decky/ui";

import { definePlugin } from "@decky/api";
import { FaBatteryHalf } from "react-icons/fa";

function Content() {
  return (
    <PanelSection title="Battery Monitor">
      <PanelSectionRow>
        <div>
          Battery monitoring is not active yet.
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <div>
          Version 0.1.0 - Development
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => {
  return {
    name: "Decky Battery Alert",

    titleView: (
      <div className={staticClasses.Title}>
        Decky Battery Alert
      </div>
    ),

    content: <Content />,

    icon: <FaBatteryHalf />,
  };
});
