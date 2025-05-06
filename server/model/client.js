const { BeanModel } = require("redbean-node/dist/bean-model");

/**
 * Client model
 */
class Client extends BeanModel {
    /**
     * Return an object that is ready to be converted to JSON
     * @returns {object} Object ready to be converted to JSON
     */
    toJSON() {
        return {
            id: this.id,
            name: this.name,
            description: this.description,
            contactName: this.contact_name,
            contactEmail: this.contact_email,
            contactPhone: this.contact_phone,
            active: Boolean(this.active),
        };
    }
}

module.exports = Client; 