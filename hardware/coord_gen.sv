module coord_gen #(
    parameter int SCREEN_W = 640,
    parameter int SCREEN_H = 480
)(
    input  logic               clk,
    input  logic               rst_n,

    input  logic [11:0]        px_x,
    input  logic [11:0]        px_y,
    input  logic               px_valid,

    input  logic signed [31:0] inv_zoom_q28,
    input  logic signed [31:0] cx_q28,
    input  logic signed [31:0] cy_q28,

    output logic               req_valid,
    output logic signed [31:0] c_re_q28,
    output logic signed [31:0] c_im_q28,
    output logic [11:0]        req_px_x,
    output logic [11:0]        req_px_y
);

    localparam int CENTER_X = SCREEN_W / 2;
    localparam int CENTER_Y = SCREEN_H / 2;
    localparam logic signed [31:0] PIXEL_UNIT_Q28 = (1 << 28) / 256;

    logic signed [31:0] dx_pix, dy_pix;
    logic signed [63:0] dx_q28_64, dy_q28_64;
    logic signed [63:0] mult_re, mult_im;
    logic signed [31:0] c_re_next, c_im_next;

    always_comb begin
        dx_pix = $signed({1'b0, px_x}) - CENTER_X;
        dy_pix = $signed({1'b0, px_y}) - CENTER_Y;

        dx_q28_64 = dx_pix * PIXEL_UNIT_Q28;  // Q4.28
        dy_q28_64 = dy_pix * PIXEL_UNIT_Q28;  // Q4.28

        mult_re = dx_q28_64 * inv_zoom_q28;   // Q8.56
        mult_im = dy_q28_64 * inv_zoom_q28;   // Q8.56

        c_re_next = cx_q28 + mult_re[55:28];
        c_im_next = cy_q28 + mult_im[55:28];
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            req_valid <= 1'b0;
            c_re_q28  <= 32'sd0;
            c_im_q28  <= 32'sd0;
            req_px_x  <= 12'd0;
            req_px_y  <= 12'd0;
        end else begin
            req_valid <= px_valid;

            if (px_valid) begin
                c_re_q28 <= c_re_next;
                c_im_q28 <= c_im_next;
                req_px_x <= px_x;
                req_px_y <= px_y;
            end
        end
    end

endmodule