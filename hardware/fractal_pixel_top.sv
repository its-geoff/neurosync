module fractal_pixel_top #(
    parameter SCREEN_W = 640,
    parameter SCREEN_H = 480,
    parameter MAX_ITER = 120
)(
    input  logic               clk,
    input  logic               rst_n,

    // VGA pixel inputs
    input  logic [11:0]        px_x,
    input  logic [11:0]        px_y,
    input  logic               px_valid,

    // parameter registers from UART / control layer (Q4.28)
    input  logic signed [31:0] zoom_q28,
    input  logic signed [31:0] center_re_q28,
    input  logic signed [31:0] center_im_q28,
    input  logic [15:0]        iter_limit,
    input  logic [7:0]         palette_id,

    // RGB output
    output logic [7:0]         out_r,
    output logic [7:0]         out_g,
    output logic [7:0]         out_b,
    output logic               pixel_ready
);

    // ----------------------------------------
    // coord_gen outputs
    // ----------------------------------------
    logic               req_valid;
    logic signed [31:0] c_re_q28;
    logic signed [31:0] c_im_q28;
    logic [11:0]        req_px_x;
    logic [11:0]        req_px_y;

    coord_gen #(
        .SCREEN_W(SCREEN_W),
        .SCREEN_H(SCREEN_H)
    ) cg (
        .clk(clk),
        .rst_n(rst_n),
        .px_x(px_x),
        .px_y(px_y),
        .px_valid(px_valid),
        .zoom_q28(zoom_q28),
        .cx_q28(center_re_q28),
        .cy_q28(center_im_q28),
        .req_valid(req_valid),
        .c_re_q28(c_re_q28),
        .c_im_q28(c_im_q28),
        .req_px_x(req_px_x),
        .req_px_y(req_px_y)
    );

    // ----------------------------------------
    // Mandelbrot core
    // ----------------------------------------
    logic start_core;
    logic core_busy, core_done;
    logic [15:0] core_iter;

    mandelbrot_core #(
        .MAX_ITER(MAX_ITER)
    ) mcore (
        .clk(clk),
        .rst_n(rst_n),
        .start(start_core),
        .c_re_q28(c_re_q28),
        .c_im_q28(c_im_q28),
        .busy(core_busy),
        .done(core_done),
        .iter_count(core_iter)
    );

    // ----------------------------------------
    // Palette LUT
    // ----------------------------------------
    logic [7:0] rgb_r_i, rgb_g_i, rgb_b_i;

    palette_lut pal (
        .clk(clk),
        .iter_in(core_iter),
        .max_iter(iter_limit),
        .palette_id(palette_id),
        .rgb_r(rgb_r_i),
        .rgb_g(rgb_g_i),
        .rgb_b(rgb_b_i)
    );

    // ----------------------------------------
    // Simple control FSM
    // ----------------------------------------
    typedef enum logic [1:0] {IDLE, WAIT_CORE, OUTPUT} state_t;
    state_t state;

    logic [11:0] out_x, out_y;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= IDLE;
            start_core  <= 1'b0;
            out_r       <= 8'd0;
            out_g       <= 8'd0;
            out_b       <= 8'd0;
            pixel_ready <= 1'b0;
            out_x       <= 12'd0;
            out_y       <= 12'd0;
        end else begin
            case (state)
                IDLE: begin
                    pixel_ready <= 1'b0;
                    start_core  <= 1'b0;

                    if (req_valid && !core_busy) begin
                        start_core <= 1'b1;   // one-cycle pulse
                        out_x <= req_px_x;
                        out_y <= req_px_y;
                        state <= WAIT_CORE;
                    end
                end

                WAIT_CORE: begin
                    start_core <= 1'b0;

                    if (core_done) begin
                        out_r <= rgb_r_i;
                        out_g <= rgb_g_i;
                        out_b <= rgb_b_i;
                        pixel_ready <= 1'b1;
                        state <= OUTPUT;
                    end
                end

                OUTPUT: begin
                    pixel_ready <= 1'b0;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule