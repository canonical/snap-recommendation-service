import { Button, Icon } from "@canonical/react-components";

export function AsideCloseButton({ close }: { close: () => void }) {
    return (
        <Button
            appearance="base"
            className="u-no-margin--bottom"
            hasIcon
            onClick={close}
        >
            <Icon name="close">Close</Icon>
        </Button>
    );
}
