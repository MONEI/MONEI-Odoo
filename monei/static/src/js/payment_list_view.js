/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class MoneiPaymentListController extends ListController {
    setup() {
        super.setup();
    }

    async onClickSync() {
        await this.actionService.doAction('monei.action_monei_sync_wizard');
    }

    async onClickLink() {
        await this.actionService.doAction('monei.action_link_orders');
    }

    async onClickCreate() {
        await this.actionService.doAction('monei.action_monei_payment_create_wizard');
    }
}

registry.category("views").add("monei_payment_list", {
    ...listView,
    Controller: MoneiPaymentListController,
    buttonTemplate: "monei.ListView.Buttons",
}); 