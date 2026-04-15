module fractal_lowres_renderer #(
    parameter H_VISIBLE = 640,
    parameter V_VISIBLE = 480,
    parameter SCALE     = 4,
    parameter MAX_ITER  = 120
)(
    input  logic               clk,
    input  logic               rst_n,

    // Incoming pixel coordinates from external VGA timing
    input  logic [9:0]         px_x,
    input  logic [9:0]         px_y,
    input  logic               px_active,

    // Fractal control parameters (Q4.28)
    input  logic signed [31:0] inv_zoom_q28,
    input  logic signed [31:0] center_re_q28,
    input  logic signed [31:0] center_im_q28,
    input  logic [15:0]        iter_limit,
    input  logic [7:0]         palette_id,

    // RGB output
    output logic [3:0]         out_red,
    output logic [3:0]         out_green,
    output logic [3:0]         out_blue
);

    localparam int FB_W    = H_VISIBLE / SCALE;
    localparam int FB_H    = V_VISIBLE / SCALE;
    localparam int FB_SIZE = FB_W * FB_H;

    // ============================================================
    // Low-res fractal pixel generator
    // Runs directly on clk (which is now the real 25 MHz clock)
    // ============================================================
    logic [11:0] render_x, render_y;
    logic        render_req;
    logic [7:0]  fract_r, fract_g, fract_b;
    logic        fract_pixel_ready;

    fractal_pixel_top #(
        .SCREEN_W (FB_W),
        .SCREEN_H (FB_H),
        .MAX_ITER (MAX_ITER)
    ) u_fractal_top (
        .clk           (clk),
        .rst_n         (rst_n),
        .ce            (1'b1),           // no extra divide here
        .px_x          (render_x),
        .px_y          (render_y),
        .px_valid      (render_req),
        .inv_zoom_q28  (inv_zoom_q28),
        .center_re_q28 (center_re_q28),
        .center_im_q28 (center_im_q28),
        .iter_limit    (iter_limit),
        .palette_id    (palette_id),
        .out_r         (fract_r),
        .out_g         (fract_g),
        .out_b         (fract_b),
        .pixel_ready   (fract_pixel_ready)
    );

    // ============================================================
    // Framebuffer: 12-bit RGB
    // ============================================================
    (* ram_style = "block" *) logic [11:0] fb_mem [0:FB_SIZE-1];

    logic        fb_we;
    logic [14:0] fb_wr_addr;
    logic [11:0] fb_wr_data;

    logic [14:0] fb_rd_addr;
    logic [11:0] fb_rd_data;

    always_ff @(posedge clk) begin
        if (fb_we)
            fb_mem[fb_wr_addr] <= fb_wr_data;
    end

    always_ff @(posedge clk) begin
        fb_rd_data <= fb_mem[fb_rd_addr];
    end

    // ============================================================
    // Background renderer FSM
    // ============================================================
    typedef enum logic [1:0] {
        R_IDLE,
        R_WAIT
    } render_state_t;

    render_state_t rstate;

    logic [11:0] cur_x, cur_y;
    logic [14:0] cur_addr;
    logic        frame_valid;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rstate      <= R_IDLE;
            render_req  <= 1'b0;
            render_x    <= 12'd0;
            render_y    <= 12'd0;
            cur_x       <= 12'd0;
            cur_y       <= 12'd0;
            cur_addr    <= 15'd0;
            fb_we       <= 1'b0;
            fb_wr_addr  <= 15'd0;
            fb_wr_data  <= 12'd0;
            frame_valid <= 1'b0;
        end else begin
            render_req <= 1'b0;
            fb_we      <= 1'b0;

            case (rstate)
                R_IDLE: begin
                    render_x   <= cur_x;
                    render_y   <= cur_y;
                    render_req <= 1'b1;
                    rstate     <= R_WAIT;
                end

                R_WAIT: begin
                    if (fract_pixel_ready) begin
                        fb_we      <= 1'b1;
                        fb_wr_addr <= cur_addr;
                        fb_wr_data <= {fract_r[7:4], fract_g[7:4], fract_b[7:4]};

                        if (cur_x == FB_W-1) begin
                            cur_x <= 12'd0;
                            if (cur_y == FB_H-1) begin
                                cur_y       <= 12'd0;
                                cur_addr    <= 15'd0;
                                frame_valid <= 1'b1;
                            end else begin
                                cur_y    <= cur_y + 12'd1;
                                cur_addr <= cur_addr + 15'd1;
                            end
                        end else begin
                            cur_x    <= cur_x + 12'd1;
                            cur_addr <= cur_addr + 15'd1;
                        end

                        rstate <= R_IDLE;
                    end
                end

                default: begin
                    rstate <= R_IDLE;
                end
            endcase
        end
    end

    // ============================================================
    // Framebuffer read / upscale
    // ============================================================
    logic [7:0] fb_x;
    logic [6:0] fb_y;

    always_comb begin
        fb_x = px_x[9:2];
        fb_y = px_y[8:2];

        // fb_rd_addr = fb_y * 160 + fb_x
        // 160 = 128 + 32
        fb_rd_addr = (fb_y << 7) + (fb_y << 5) + fb_x;
    end

    // ============================================================
    // Align active signal to synchronous framebuffer read
    // ============================================================
    logic px_active_d;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            px_active_d <= 1'b0;
        else
            px_active_d <= px_active;
    end

    // ============================================================
    // Output gating
    // ============================================================
    assign out_red   = (px_active_d && frame_valid) ? fb_rd_data[11:8] : 4'd0;
    assign out_green = (px_active_d && frame_valid) ? fb_rd_data[7:4]  : 4'd0;
    assign out_blue  = (px_active_d && frame_valid) ? fb_rd_data[3:0]  : 4'd0;

endmodule